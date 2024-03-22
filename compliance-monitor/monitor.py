#!/usr/bin/env python3
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
import json
import os
import os.path
import secrets
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import psycopg2
from psycopg2.errors import UniqueViolation
import ruamel.yaml
import uvicorn


class Settings:
    def __init__(self):
        self.db_host = os.getenv("SCM_DB_HOST", "localhost")
        self.db_user = os.getenv("SCM_DB_USER", "postgres")
        self.db_password = os.getenv("SCM_DB_PASSWORD", "mysecretpassword")
        self.bootstrap_path = os.path.abspath("./bootstrap.yaml")
        self.yaml_path = os.path.abspath("../Tests")


ROLES = {'read_any': 1, 'append_any': 2, 'admin': 4, 'approve': 8}
# number of days that expired results will be considered in lieu of more recent, but unapproved ones
GRACE_PERIOD_DAYS = 7


# do I hate these globals, but I don't see another way with these frameworks
app = FastAPI()
security = HTTPBasic(realm="Compliance monitor", auto_error=True)
optional_security = HTTPBasic(realm="Compliance monitor", auto_error=False)
settings = Settings()


class TimestampEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return str(obj)
        # Let the base class default method raise the TypeError
        return super().default(obj)


def mk_conn(settings=settings):
    return psycopg2.connect(host=settings.db_host, user=settings.db_user, password=settings.db_password)


def get_conn(settings=settings):
    conn = mk_conn(settings=settings)
    try:
        yield conn
    finally:
        conn.close()


def get_current_account(
    credentials: Optional[HTTPBasicCredentials],
    conn: psycopg2.extensions.connection,
):
    if credentials is None:
        return
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT apikey, publickey, roles FROM account WHERE subject = %s;
                ''',
                (credentials.username, )
            )
            if not cur.rowcount:
                raise RuntimeError
            apikey, publickey, roles = cur.fetchone()
        current_password_bytes = credentials.password.encode("utf8")
        is_correct_password = secrets.compare_digest(
            current_password_bytes, apikey.encode("utf8")
        )
        if not is_correct_password:
            raise RuntimeError
        return credentials.username, publickey, roles
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": f"Basic {security.realm}"},
        )


def ensure_schema(conn):
    # strive to make column names unique across tables so that selects become simple, such as:
    # select * from "check" natural join standardentry natural join version natural join scope;
    with conn.cursor() as cur:
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS account (
                subject text PRIMARY KEY,
                apikey text,
                publickey text,
                roles integer
            );
            CREATE TABLE IF NOT EXISTS scope (
                scopeid SERIAL PRIMARY KEY,
                scopeuuid text UNIQUE,
                scope text,
                url text
            );
            CREATE TABLE IF NOT EXISTS version (
                versionid SERIAL PRIMARY KEY,
                scopeid integer NOT NULL REFERENCES scope ON DELETE CASCADE ON UPDATE CASCADE,
                version text,
                stabilized_at date,
                deprecated_at date,
                UNIQUE (scopeid, version)
            );
            CREATE TABLE IF NOT EXISTS standardentry (
                standardid SERIAL PRIMARY KEY,
                versionid integer NOT NULL REFERENCES version ON DELETE CASCADE ON UPDATE CASCADE,
                standard text,
                surl text,  -- don't name it url to avoid clash with scope.url
                condition text,
                UNIQUE (versionid, surl)
            );
            CREATE TABLE IF NOT EXISTS "check" (
                checkid SERIAL PRIMARY KEY,
                -- the versionid field is redundant given the standardid field, but we need it for
                -- the constraint at the bottom :(
                versionid integer NOT NULL REFERENCES version ON DELETE CASCADE ON UPDATE CASCADE,
                standardid integer NOT NULL REFERENCES standardentry ON DELETE CASCADE ON UPDATE CASCADE,
                id text,
                lifetime text,
                ccondition text,  -- don't name it condition to avoid clash with standardentry.condition
                UNIQUE (versionid, id)
            );
            CREATE TABLE IF NOT EXISTS report (
                reportid SERIAL PRIMARY KEY,
                reportuuid text UNIQUE,
                checked_at timestamp,
                subject text,
                -- scopeid integer NOT NULL REFERENCES scope ON DELETE CASCADE ON UPDATE CASCADE,
                -- let's omit the scope here because it is determined via the results, and it
                -- is possible that future reports refer to multiple scopes
                data jsonb,
                rawformat text,
                raw bytea
            );
            CREATE TABLE IF NOT EXISTS invocation (
                invocationid SERIAL PRIMARY KEY,
                reportid integer NOT NULL REFERENCES report ON DELETE CASCADE ON UPDATE CASCADE,
                invocation text,
                critical integer,
                error integer,
                warning integer,
                result integer
            );
            CREATE TABLE IF NOT EXISTS result (
                resultid SERIAL PRIMARY KEY,
                checkid integer NOT NULL REFERENCES "check" ON DELETE CASCADE ON UPDATE CASCADE,
                result int,
                approval boolean,  -- whether a result <> 1 has manual approval
                expiration timestamp,  -- precompute when this result would be expired
                invocationid integer REFERENCES invocation ON DELETE CASCADE ON UPDATE CASCADE,
                -- note that invocation is more like an implementation detail
                -- therefore let's also put reportid here (added bonus: simplify queries)
                reportid integer NOT NULL REFERENCES report ON DELETE CASCADE ON UPDATE CASCADE
            );
            '''
        )


def import_bootstrap(bootstrap_path, conn):
    ryaml = ruamel.yaml.YAML()
    with open(bootstrap_path) as fp:
        data = ryaml.load(fp)
    if not data or not isinstance(data, dict):
        return
    accounts = data.get('accounts')
    if not accounts:
        return
    with conn.cursor() as cur:
        for account in accounts:
            roles = sum(ROLES[r] for r in account.get('roles', ()))
            cur.execute(
                '''
                INSERT INTO account (subject, apikey, publickey, roles)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (subject)
                DO UPDATE
                SET apikey = EXCLUDED.apikey, publickey = EXCLUDED.publickey, roles = EXCLUDED.roles;
                ''',
                (account['subject'], account['api_key'], account['public_key'], roles),
            )
        conn.commit()


def import_cert_yaml(yaml_path, conn):
    yaml = ruamel.yaml.YAML(typ='safe')
    with open(yaml_path, "r") as fileobj:
        document = yaml.load(fileobj.read())
    # The following will update any existing entries (such as versions, standards, checks),
    # but it won't delete entries that are not present in the given yaml.
    # We will do that in a second step. (Note that deletions will cascade to reports, but we should
    # only ever delete entries for non-stable versions; stable versions are deemed immutable except
    # maybe for checks, and for those, at least the ids are immutable.)
    # It is paramount that all extant primary keys are kept because the reports refer to them.
    with conn.cursor() as cur:
        cur.execute(
            '''
            INSERT INTO scope (scopeuuid, scope, url)
            VALUES (%s, %s, %s)
            ON CONFLICT (scopeuuid)
            DO UPDATE
            SET scope = EXCLUDED.scope, url = EXCLUDED.url
            RETURNING scopeid;
            ''',
            (document['uuid'], document['name'], document['url']),
        )
        scopeid, = cur.fetchone()
        all_versions = set()
        for vdata in document['versions']:
            all_versions.add(vdata['version'])            
            cur.execute(
                '''
                INSERT INTO version (scopeid, version, stabilized_at, deprecated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (scopeid, version)
                DO UPDATE
                SET stabilized_at = EXCLUDED.stabilized_at, deprecated_at = EXCLUDED.deprecated_at
                RETURNING versionid;
                ''',
                (scopeid, vdata['version'], vdata.get('stabilized_at'), vdata.get('deprecated_at')),
            )
            versionid, = cur.fetchone()
            all_standards = set()
            for sdata in vdata['standards']:
                all_standards.add(sdata['url'])
                cur.execute(
                    '''
                    INSERT INTO standardentry (versionid, standard, surl, condition)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (versionid, surl)
                    DO UPDATE
                    SET condition = EXCLUDED.condition, standard = EXCLUDED.standard
                    RETURNING standardid;
                    ''',
                    (versionid, sdata['name'], sdata['url'], sdata.get('condition')),
                )
                standardid, = cur.fetchone()
                all_checks = set()
                for cdata in sdata.get('checks', ()):
                    all_checks.add(cdata['id'])
                    cur.execute(
                        '''
                        INSERT INTO "check" (versionid, standardid, id, lifetime, ccondition)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (versionid, id)
                        DO UPDATE
                        SET ccondition = EXCLUDED.ccondition, lifetime = EXCLUDED.lifetime
                        ''',
                        (versionid, standardid, cdata['id'], cdata.get('lifetime'), cdata.get('condition')),
                    )
                cur.execute(
                    '''
                    SELECT checkid, id FROM "check" WHERE standardid = %s;
                    ''',
                    (standardid, )
                )
                removeids = [checkid for checkid, id_ in cur.fetchall() if id_ not in all_checks]
                while removeids:
                    cur.execute('DELETE FROM "check" WHERE checkid IN %s', (tuple(removeids[:10]), ))
                    del removeids[:10]
            cur.execute(
                '''
                SELECT standardid, surl FROM standardentry WHERE versionid = %s;
                ''',
                (versionid, )
            )
            removeids = [standardid for standardid, surl in cur.fetchall() if surl not in all_standards]
            while removeids:
                cur.execute('DELETE FROM standardentry WHERE standardid IN %s', (tuple(removeids[:10]), ))
                del removeids[:10]
        cur.execute(
            '''
            SELECT versionid, version FROM version WHERE scopeid = %s;
            ''',
            (scopeid, )
        )
        removeids = [versionid for versionid, version in cur.fetchall() if version not in all_versions]
        while removeids:
            cur.execute('DELETE FROM version WHERE versionid IN %s', (tuple(removeids[:10]), ))
            del removeids[:10]
        conn.commit()


def import_cert_yaml_dir(yaml_path, conn):
    for fn in sorted(os.listdir(yaml_path)):
        if fn.startswith('scs-') and fn.endswith('.yaml'):
            import_cert_yaml(os.path.join(yaml_path, fn), conn)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/reports")
async def get_reports(
    request: Request,
    subject: Optional[str] = None, limit: int = 10, skip: int = 0,
    conn: psycopg2.extensions.connection = Depends(get_conn),
):
    account = get_current_account(await security(request), conn)
    current_subject, publickey, roles = account
    if subject is None:
        subject = current_subject
    elif subject != current_subject and ROLES['read_any'] & roles == 0:
        raise HTTPException(status_code=401, detail="Permission denied")
    with conn.cursor() as cur:
        if subject != '':
            cur.execute('SELECT data FROM report WHERE subject = %s LIMIT %s OFFSET %s;', (subject, limit, skip))
        else:
            cur.execute('SELECT data FROM report LIMIT %s OFFSET %s;', (limit, skip))
        return [row[0] for row in cur.fetchall()]


def add_period(dt: datetime, period: str):
    # compute the moment of expiry (so we are valid before that point, but not on that point)
    if period == 'day':
        dt += timedelta(days=2)
        return datetime(dt.year, dt.month, dt.day)
    if period == 'week':
        dt += timedelta(days=14 - dt.weekday())
        return datetime(dt.year, dt.month, dt.day)
    if period == 'month':
        if dt.month == 11:
            return datetime(dt.year + 1, 1, 1)
        if dt.month == 12:
            return datetime(dt.year + 1, 2, 1)
        return datetime(dt.year, dt.month + 2, 1)
    if period == 'quarter':
        if dt.month >= 10:
            return datetime(dt.year + 1, 4, 1)
        if dt.month >= 7:
            return datetime(dt.year + 1, 1, 1)
        if dt.month >= 4:
            return datetime(dt.year, 10, 1)
        return datetime(dt.year, 7, 1)


@app.post("/reports")
async def post_report(
    request: Request,
    conn: psycopg2.extensions.connection = Depends(get_conn),
):
    account = get_current_account(await security(request), conn)
    current_subject, publickey, roles = account
    # test this like so:
    # curl --data-binary @blubb.yaml -H "Content-Type: application/yaml" -H "Authorization: Basic YWRtaW46c2VjcmV0IGFwaSBrZXk=" http://127.0.0.1:8080/reports
    content_type = request.headers['content-type']
    if content_type not in ('application/yaml', 'application/json'):
        raise HTTPException(status_code=500, detail="Unsupported content type")
    body = await request.body()
    body_text = body.decode("utf-8")
    json_text = None
    if content_type.endswith('/yaml'):
        yaml = ruamel.yaml.YAML(typ='safe')
        document = yaml.load(body_text)
        json_text = json.dumps(document, cls=TimestampEncoder)
    elif content_type.endswith("/json"):
        document = json.loads(body_text)
        json_text = body_text
    else:
        raise HTTPException(status_code=500)
    rundata = document['run']
    uuid, subject, checked_at = rundata['uuid'], document['subject'], document['checked_at']
    if subject != current_subject and ROLES['append_any'] & roles == 0:
        raise HTTPException(status_code=401, detail="Permission denied")
    expiration_lookup = {
        period: add_period(checked_at, period)
        for period in ('day', 'week', 'month', 'quarter')
    }
    expiration_lookup[None] = expiration_lookup['day']  # default
    scopeuuid = document['spec']['uuid']
    with conn.cursor() as cur:
        cur.execute('SELECT scopeid FROM scope WHERE scopeuuid = %s;', (scopeuuid, ))
        scopeid, = cur.fetchone()
        try:
            cur.execute(
                '''
                INSERT INTO report (reportuuid, checked_at, subject, data, rawformat, raw)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING reportid;
                ''',
                (uuid, checked_at, subject, json_text, content_type, body),
            )
        except UniqueViolation:
            raise HTTPException(status_code=409, detail="Conflict: report already present")
        reportid, = cur.fetchone()
        invocation_ids = {}
        for invocation, idata in rundata['invocations'].items():
            cur.execute(
                '''
                INSERT INTO invocation (reportid, invocation, critical, error, warning, result)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING invocationid;
                ''',
                (reportid, invocation, idata['critical'], idata['error'], idata['warning'], idata['result']),
            )
            invocationid, = cur.fetchone()
            invocation_ids[invocation] = invocationid
        for version, vdata in document['versions'].items():
            cur.execute('SELECT versionid FROM version WHERE scopeid = %s AND version = %s;', (scopeid, version))
            versionid, = cur.fetchone()
            for check, rdata in vdata.items():
                cur.execute('SELECT checkid, lifetime FROM "check" WHERE versionid = %s AND id = %s;', (versionid, check))
                checkid, lifetime = cur.fetchone()
                expiration = expiration_lookup[lifetime]
                invocationid = invocation_ids[rdata['invocation']]
                result = rdata['result']
                approval = 1 == result  # pre-approve good result
                cur.execute(
                    '''
                    INSERT INTO result (reportid, invocationid, checkid, result, approval, expiration)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING resultid;
                    ''',
                    (reportid, invocationid, checkid, result, approval, expiration),
                )
                resultid, = cur.fetchone()
    conn.commit()


@app.get("/status/{subject}")
async def get_status(
    request: Request,
    subject: str,
    scopeuuid: str = None, version: str = None,
    conn: psycopg2.extensions.connection = Depends(get_conn),
):
    # note: text/html will be the default, but let's start with json to get the logic right
    accept = request.headers['accept']
    if 'application/json' not in accept and '*/*' not in accept:
        raise HTTPException(status_code=500, detail="client needs to accept application/json")
    account = get_current_account(await optional_security(request), conn)
    if account:
        current_subject, publickey, roles = account
    else:
        current_subject, publickey, roles = None, None, 0
    is_privileged = subject == current_subject or ROLES['read_any'] & roles != 0
    with conn.cursor() as cur:
        # this will list all scopes, versions, checks
        # plus, where available, the latest test result (if necessary, with manual approval)
        cur.execute(
            f'''
            SELECT scope.scopeuuid, scope.scope, version.version, standardentry.condition, "check".id, "check".ccondition, latest.result, latest.approval
            FROM "check"
            NATURAL JOIN standardentry
            NATURAL JOIN version
            NATURAL JOIN scope
            LEFT OUTER JOIN (
                -- find the latest result per checkid for this subject
                -- DISTINCT ON is a Postgres-specific construct that comes in very handy here :)
                SELECT DISTINCT ON (checkid) *
                FROM result
                NATURAL JOIN report
                WHERE subject = %s
                AND expiration > {'NOW()' if is_privileged else f"NOW() - interval '{GRACE_PERIOD_DAYS:d} days'"}
                {'' if is_privileged else 'AND approval'}
                ORDER BY checkid, checked_at DESC
            ) latest
            ON "check".checkid = latest.checkid
            {'' if scopeuuid is None and version is None else 'WHERE'}
            {'' if scopeuuid is None else 'scope.scopeuuid = %s'}
            {'' if scopeuuid is None or version is None else 'AND'}
            {'' if version is None else 'version.version = %s'}
            ;
            ''',
            (subject, ) + (() if scopeuuid is None else (scopeuuid, )) + (() if version is None else (version, )),
        )
        rows = cur.fetchall()
    # now collect pass, DNF, fail per scope/version
    num_pass, num_dnf, num_fail = defaultdict(set), defaultdict(set), defaultdict(set)
    # also collect some ancillary information
    scopes = {}
    for scopeuuid, scope, version, condition, check, ccondition, result, approval in rows:
        scopes.setdefault(scopeuuid, scope)
        if result is not None and (condition == "optional" or ccondition == "optional"):
            # count optional as 'pass' so long as a result is available;
            # otherwise a version without mandatory checks wouldn't be counted at all
            num_pass[(scopeuuid, version)].add(check)
        elif result == 1:
            num_pass[(scopeuuid, version)].add(check)
        elif result == -1:
            num_fail[(scopeuuid, version)].add(check)
        else:
            num_dnf[(scopeuuid, version)].add(check)
    results = {}
    for scopeuuid, scope in scopes.items():
        results[scopeuuid] = {"name": scope, "versions": defaultdict(dict), "result": 0}
    keys = sorted(set(num_pass) | set(num_dnf) | set(num_fail))
    for key in keys:
        result = -1 if key in num_fail else 0 if key in num_dnf else 1
        scopeuuid, version = key
        results[scopeuuid]["versions"][version] = result
        if result == 1:
            # FIXME also check that the version is valid
            results[scopeuuid]["result"] = 1
    return results


@app.get("/results")
async def get_results(
    request: Request,
    approved: Optional[bool] = None, limit: int = 10, skip: int = 0,
    conn: psycopg2.extensions.connection = Depends(get_conn),
):
    """get recent results, potentially filtered by approval status"""
    account = get_current_account(await security(request), conn)
    current_subject, publickey, roles = account
    if ROLES['read_any'] & roles == 0:
        raise HTTPException(status_code=401, detail="Permission denied")
    with conn.cursor() as cur:
        columns = ('reportuuid', 'subject', 'checked_at', 'scopeuuid', 'version', 'check', 'result', 'approval')
        cur.execute(
            f'''
            SELECT report.reportuuid, report.subject, report.checked_at, scope.scopeuuid, version.version, "check".id, result.result, result.approval
            FROM result
            NATURAL JOIN report
            NATURAL JOIN "check"
            NATURAL JOIN standardentry
            NATURAL JOIN version
            NATURAL JOIN scope
            WHERE expiration > NOW() - interval '{GRACE_PERIOD_DAYS:d} days'
            {'' if approved is None else f'AND approval = {str(bool(approved))}'}
            ORDER BY checked_at
            LIMIT %s OFFSET %s;
            ''',
            (limit, skip)
        )
        return [{col: val for col, val in zip(columns, row)} for row in cur.fetchall()]


@app.post("/results")
async def post_results(
    request: Request,
    conn: psycopg2.extensions.connection = Depends(get_conn),
):
    """post approvals to this endpoint"""
    content_type = request.headers['content-type']
    if content_type not in ('application/json', ):
        raise HTTPException(status_code=500, detail="Unsupported content type")
    body = await request.body()
    document = json.loads(body.decode("utf-8"))
    records = [document] if isinstance(document, dict) else document
    account = get_current_account(await security(request), conn)
    current_subject, publickey, roles = account
    if ROLES['approve'] & roles == 0:
        raise HTTPException(status_code=401, detail="Permission denied")
    with conn.cursor() as cur:
        resultids = []
        for record in records:
            reportuuid, scopeuuid, version, check, approval = [
                record[key]
                for key in ['reportuuid', 'scopeuuid', 'version', 'check', 'approval']
            ]
            cur.execute(
                f'''
                UPDATE result
                SET approval = %s
                FROM report, scope, version, "check"
                WHERE report.reportuuid = %s
                AND result.reportid = report.reportid
                AND scope.scopeuuid = %s
                AND version.scopeid = scope.scopeid
                AND version.version = %s
                AND "check".versionid = version.versionid
                AND "check".id = %s
                AND result.checkid = "check".checkid
                RETURNING resultid;
                ''',
                (approval, reportuuid, scopeuuid, version, check)
            )
            resultid, = cur.fetchone()
            resultids.append(resultid)
    conn.commit()


if __name__ == "__main__":
    with mk_conn(settings=settings) as conn:
        ensure_schema(conn=conn)
        import_bootstrap(settings.bootstrap_path, conn=conn)
        import_cert_yaml_dir(settings.yaml_path, conn=conn)
    uvicorn.run(app, port=8080, log_level="info", workers=1)
