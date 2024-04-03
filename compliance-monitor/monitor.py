#!/usr/bin/env python3
from collections import defaultdict
from datetime import date, datetime, timedelta
import json
import os
import os.path
import secrets
from shutil import which
from subprocess import run
from tempfile import NamedTemporaryFile
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import psycopg2
from psycopg2.errors import UniqueViolation
from psycopg2 import sql
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
# separator between signature and report data; use something like
#     ssh-keygen \
#       -Y sign -f ~/.ssh/id_ed25519 -n report myreport.yaml
#     curl \
#       --data-binary @myreport.yaml.sig --data-binary @myreport.yaml \
#       -H "Content-Type: application/yaml" -H "Authorization: Basic ..." \
#       http://127.0.0.1:8080/reports
# to achieve this!
SEP = "-----END SSH SIGNATURE-----\n&"


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


# use ... (Ellipsis) here to indicate that no default value exists (will lead to error if no value is given)
ACCOUNT_DEFAULTS = {'subject': ..., 'api_key': ..., 'roles': ...}
PUBLIC_KEY_DEFAULTS = {'public_key': ..., 'public_key_type': ..., 'public_key_name': ...}
SCOPE_DEFAULTS = {'uuid': ..., 'name': ..., 'url': ...}
VERSION_DEFAULTS = {'version': ..., 'stabilized_at': None, 'deprecated_at': None}
STANDARD_DEFAULTS = {'name': ..., 'url': ..., 'condition': None}
CHECK_DEFAULTS = {'id': ..., 'lifetime': None, 'condition': None}
INVOCATION_DEFAULTS = {'critical': ..., 'error': ..., 'warning': ..., 'result': ...}


def sanitize_record(record, defaults, **kwargs):
    sanitized = {key: record.get(key, value) for key, value in defaults.items()}
    sanitized.update(**kwargs)
    return sanitized


def make_where_clause(*filter_clauses):
    """join args of type sql.Composable via AND, dropping None, and prepend WHERE if appropriate"""
    clause = sql.SQL(' AND ').join(filter(None, filter_clauses))
    return sql.SQL(' WHERE {} ').format(clause) if clause.seq else sql.SQL('')


def db_find_account(cur: psycopg2.extensions.cursor, subject):
    cur.execute('''
    SELECT apikey, roles
    FROM account
    WHERE subject = %s;''', (subject, ))
    return cur.fetchone()


def db_get_keys(cur: psycopg2.extensions.cursor, subject):
    cur.execute('''
    SELECT keytype, key
    FROM publickey
    NATURAL JOIN account
    WHERE subject = %s;''', (subject, ))
    return cur.fetchall()


def db_ensure_schema(cur: psycopg2.extensions.cursor):
    # strive to make column names unique across tables so that selects become simple, such as:
    # select * from "check" natural join standardentry natural join version natural join scope;
    cur.execute('''
    CREATE TABLE IF NOT EXISTS account (
        accountid SERIAL PRIMARY KEY,
        subject text UNIQUE,
        apikey text,
        roles integer
    );
    CREATE TABLE IF NOT EXISTS publickey (
        keyid SERIAL PRIMARY KEY,
        key text,
        keytype text,
        keyname text,
        accountid integer NOT NULL REFERENCES account ON DELETE CASCADE ON UPDATE CASCADE,
        UNIQUE (accountid, keyname)
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
    ''')


def db_update_account(cur: psycopg2.extensions.cursor, record: dict):
    sanitized = sanitize_record(record, ACCOUNT_DEFAULTS)
    cur.execute('''
    INSERT INTO account (subject, apikey, roles)
    VALUES (%(subject)s, %(api_key)s, %(roles)s)
    ON CONFLICT (subject)
    DO UPDATE
    SET apikey = EXCLUDED.apikey
    , roles = EXCLUDED.roles
    RETURNING accountid;''', sanitized)
    accountid, = cur.fetchone()
    return accountid


def db_update_publickey(cur: psycopg2.extensions.cursor, accountid, record: dict):
    sanitized = sanitize_record(record, PUBLIC_KEY_DEFAULTS, accountid=accountid)
    cur.execute('''
    INSERT INTO publickey (key, keytype, keyname, accountid)
    VALUES (%(public_key)s, %(public_key_type)s, %(public_key_name)s, %(accountid)s)
    ON CONFLICT (accountid, keyname)
    DO UPDATE
    SET key = EXCLUDED.key
    , keytype = EXCLUDED.keytype
    , keyname = EXCLUDED.keyname
    RETURNING keyid;''', sanitized)
    keyid, = cur.fetchone()
    return keyid


def db_filter_publickeys(cur: psycopg2.extensions.cursor, accountid, predicate: callable):
    cur.execute('SELECT keyid, keyname FROM publickey WHERE accountid = %s;', (accountid, ))
    removeids = [row[0] for row in cur.fetchall() if not predicate(*row)]
    while removeids:
        cur.execute('DELETE FROM publickey WHERE keyid IN %s', (tuple(removeids[:10]), ))
        del removeids[:10]


def db_update_scope(cur: psycopg2.extensions.cursor, record: dict):
    sanitized = sanitize_record(record, SCOPE_DEFAULTS)
    cur.execute('''
    INSERT INTO scope (scopeuuid, scope, url)
    VALUES (%(uuid)s, %(name)s, %(url)s)
    ON CONFLICT (scopeuuid)
    DO UPDATE
    SET scope = EXCLUDED.scope, url = EXCLUDED.url
    RETURNING scopeid;''', sanitized)
    scopeid, = cur.fetchone()
    return scopeid


def db_update_version(cur: psycopg2.extensions.cursor, scopeid, record: dict):
    sanitized = sanitize_record(record, VERSION_DEFAULTS, scopeid=scopeid)
    cur.execute('''
    INSERT INTO version (scopeid, version, stabilized_at, deprecated_at)
    VALUES (%(scopeid)s, %(version)s, %(stabilized_at)s, %(deprecated_at)s)
    ON CONFLICT (scopeid, version)
    DO UPDATE
    SET stabilized_at = EXCLUDED.stabilized_at, deprecated_at = EXCLUDED.deprecated_at
    RETURNING versionid;''', sanitized)
    versionid, = cur.fetchone()
    return versionid


def db_update_standard(cur: psycopg2.extensions.cursor, versionid, record: dict):
    sanitized = sanitize_record(record, STANDARD_DEFAULTS, versionid=versionid)
    cur.execute('''
    INSERT INTO standardentry (versionid, standard, surl, condition)
    VALUES (%(versionid)s, %(name)s, %(url)s, %(condition)s)
    ON CONFLICT (versionid, surl)
    DO UPDATE
    SET condition = EXCLUDED.condition, standard = EXCLUDED.standard
    RETURNING standardid;''', sanitized)
    standardid, = cur.fetchone()
    return standardid


def db_update_check(cur: psycopg2.extensions.cursor, versionid, standardid, record: dict):
    sanitized = sanitize_record(record, CHECK_DEFAULTS, versionid=versionid, standardid=standardid)
    cur.execute('''
    INSERT INTO "check" (versionid, standardid, id, lifetime, ccondition)
    VALUES (%(versionid)s, %(standardid)s, %(id)s, %(lifetime)s, %(condition)s)
    ON CONFLICT (versionid, id)
    DO UPDATE
    SET ccondition = EXCLUDED.ccondition, lifetime = EXCLUDED.lifetime
    RETURNING checkid;''', sanitized)
    checkid, = cur.fetchone()
    return checkid


def db_filter_checks(cur: psycopg2.extensions.cursor, standardid, predicate: callable):
    cur.execute('SELECT checkid, id FROM "check" WHERE standardid = %s;', (standardid, ))
    removeids = [row[0] for row in cur.fetchall() if not predicate(*row)]
    while removeids:
        cur.execute('DELETE FROM "check" WHERE checkid IN %s', (tuple(removeids[:10]), ))
        del removeids[:10]


def db_filter_standards(cur: psycopg2.extensions.cursor, versionid, predicate: callable):
    cur.execute('SELECT standardid, surl FROM standardentry WHERE versionid = %s;', (versionid, ))
    removeids = [row[0] for row in cur.fetchall() if not predicate(*row)]
    while removeids:
        cur.execute('DELETE FROM standardentry WHERE standardid IN %s', (tuple(removeids[:10]), ))
        del removeids[:10]


def db_filter_versions(cur: psycopg2.extensions.cursor, scopeid, predicate: callable):
    cur.execute('SELECT versionid, version FROM version WHERE scopeid = %s;', (scopeid, ))
    removeids = [row[0] for row in cur.fetchall() if not predicate(*row)]
    while removeids:
        cur.execute('DELETE FROM version WHERE versionid IN %s', (tuple(removeids[:10]), ))
        del removeids[:10]


def db_get_reports(cur: psycopg2.extensions.cursor, subject, limit, skip):
    cur.execute(
        sql.SQL("SELECT data FROM report {} LIMIT %(limit)s OFFSET %(skip)s;")
        .format(make_where_clause(
            None if not subject else sql.SQL('subject = %(subject)s'),
        )),
        {"subject": subject, "limit": limit, "skip": skip},
    )
    return [row[0] for row in cur.fetchall()]


def db_get_scopeid(cur: psycopg2.extensions.cursor, scopeuuid):
    cur.execute('SELECT scopeid FROM scope WHERE scopeuuid = %s;', (scopeuuid, ))
    scopeid, = cur.fetchone()
    return scopeid


def db_insert_report(
    cur: psycopg2.extensions.cursor, uuid, checked_at, subject, json_text, content_type, body,
):
    # this is an exception in that we don't use a record parameter (it's just not as practical here)
    cur.execute('''
    INSERT INTO report (reportuuid, checked_at, subject, data, rawformat, raw)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING reportid;''', (uuid, checked_at, subject, json_text, content_type, body))
    reportid, = cur.fetchone()
    return reportid


def db_insert_invocation(cur: psycopg2.extensions.cursor, reportid, invocation, record):
    sanitized = sanitize_record(record, INVOCATION_DEFAULTS, reportid=reportid, invocation=invocation)
    cur.execute('''
    INSERT INTO invocation (reportid, invocation, critical, error, warning, result)
    VALUES (%(reportid)s, %(invocation)s, %(critical)s, %(error)s, %(warning)s, %(result)s)
    RETURNING invocationid;''', sanitized)
    invocationid, = cur.fetchone()
    return invocationid


def db_get_versionid(cur: psycopg2.extensions.cursor, scopeid, version):
    cur.execute('SELECT versionid FROM version WHERE scopeid = %s AND version = %s;', (scopeid, version))
    versionid, = cur.fetchone()
    return versionid


def db_get_checkdata(cur: psycopg2.extensions.cursor, versionid, check):
    cur.execute('SELECT checkid, lifetime FROM "check" WHERE versionid = %s AND id = %s;', (versionid, check))
    return cur.fetchone()


def db_insert_result(
    cur: psycopg2.extensions.cursor, reportid, invocationid, checkid, result, approval, expiration,
):
    # this is an exception in that we don't use a record parameter (it's just not as practical here)
    cur.execute('''
    INSERT INTO result (reportid, invocationid, checkid, result, approval, expiration)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING resultid;''', (reportid, invocationid, checkid, result, approval, expiration))
    resultid, = cur.fetchone()
    return resultid


def db_get_relevant_results(
    cur: psycopg2.extensions.cursor,
    subject, scopeuuid, version, approved_only=True, grace_period_days=None,
):
    """for each combination of scope/version/check, get the most recent test result that is still valid"""
    cur.execute(sql.SQL('''
    SELECT scope.scopeuuid, scope.scope, version.version, standardentry.condition
    , "check".id, "check".ccondition, latest.result
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
        {report_filter}
        ORDER BY checkid, checked_at DESC
    ) latest
    ON "check".checkid = latest.checkid
    {filter_condition};''').format(
        filter_condition=make_where_clause(
            None if scopeuuid is None else sql.SQL('scope.scopeuuid = %(scopeuuid)s'),
            None if version is None else sql.SQL('version.version = %(version)s'),
        ),
        report_filter=make_where_clause(
            sql.SQL('subject = %(subject)s'),
            sql.SQL('approval') if approved_only else None,
            sql.SQL(
                'expiration > NOW()' if grace_period_days is None else
                f"expiration > NOW() - interval '{grace_period_days:d} days'"
            ),
        ),
    ), {"subject": subject, "scopeuuid": scopeuuid, "version": version})
    return cur.fetchall()


def db_get_recent_results(cur: psycopg2.extensions.cursor, approved, limit, skip):
    """list recent test results without grouping by scope/version/check"""
    columns = ('reportuuid', 'subject', 'checked_at', 'scopeuuid', 'version', 'check', 'result', 'approval')
    cur.execute(sql.SQL('''
    SELECT report.reportuuid, report.subject, report.checked_at, scope.scopeuuid, version.version
    , "check".id, result.result, result.approval
    FROM result
    NATURAL JOIN report
    NATURAL JOIN "check"
    NATURAL JOIN standardentry
    NATURAL JOIN version
    NATURAL JOIN scope
    {where_clause}
    ORDER BY checked_at
    LIMIT %(limit)s OFFSET %(skip)s;''').format(
        where_clause=make_where_clause(
            sql.SQL(f"expiration > NOW() - interval '{GRACE_PERIOD_DAYS:d} days'"),
            None if approved is None else sql.SQL('approval = %(approved)s'),
        ),
    ), {"limit": limit, "skip": skip, "approved": approved})
    return [{col: val for col, val in zip(columns, row)} for row in cur.fetchall()]


def db_patch_approval(cur: psycopg2.extensions.cursor, record):
    cur.execute('''
    UPDATE result
    SET approval = %(approval)s
    FROM report, scope, version, "check"
    WHERE report.reportuuid = %(reportuuid)s
      AND result.reportid = report.reportid
      AND scope.scopeuuid = %(scopeuuid)s
      AND version.scopeid = scope.scopeid
      AND version.version = %(version)s
      AND "check".versionid = version.versionid
      AND "check".id = %(check)s
      AND result.checkid = "check".checkid
    RETURNING resultid;''', record)
    resultid, = cur.fetchone()
    return resultid


def ssh_validate(keys, signature, data):
    # based on https://www.agwa.name/blog/post/ssh_signatures
    with NamedTemporaryFile(mode="w") as allowed_signers_file, \
            NamedTemporaryFile(mode="w") as report_sig_file, \
            NamedTemporaryFile(mode="w") as report_file:
        allowed_signers_file.write("".join([
            f"mail@csp.eu {publickey_type} {publickey}\n"
            for publickey_type, publickey in keys
        ]))
        allowed_signers_file.flush()
        report_sig_file.write(signature)
        report_sig_file.flush()
        report_file.write(data)
        report_file.flush()
        report_file.seek(0)
        if run([
            which("ssh-keygen"),
            "-Y", "verify", "-f", allowed_signers_file.name, "-I", "mail@csp.eu", "-n", "report",
            "-s", report_sig_file.name,
        ], stdin=report_file).returncode:
            raise ValueError


def get_current_account(
    credentials: Optional[HTTPBasicCredentials],
    conn: psycopg2.extensions.connection,
):
    if credentials is None:
        return
    try:
        with conn.cursor() as cur:
            row = db_find_account(cur, credentials.username)
        if not row:
            raise RuntimeError
        apikey, roles = row
        current_password_bytes = credentials.password.encode("utf8")
        is_correct_password = secrets.compare_digest(
            current_password_bytes, apikey.encode("utf8")
        )
        if not is_correct_password:
            raise RuntimeError
        return credentials.username, roles
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": f"Basic {security.realm}"},
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
            accountid = db_update_account(cur, {**account, "roles": roles})
            keyids = set(db_update_publickey(cur, accountid, key) for key in account.get("keys", ()))
            db_filter_publickeys(cur, accountid, lambda keyid, *_: keyid in keyids)
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
        scopeid = db_update_scope(cur, document)
        all_versions = set()
        for vdata in document['versions']:
            versionid = db_update_version(cur, scopeid, vdata)
            all_versions.add(versionid)
            all_standards = set()
            for sdata in vdata['standards']:
                standardid = db_update_standard(cur, versionid, sdata)
                all_standards.add(standardid)
                all_checks = set()
                for cdata in sdata.get('checks', ()):
                    checkid = db_update_check(cur, versionid, standardid, cdata)
                    all_checks.add(checkid)
                db_filter_checks(cur, standardid, lambda checkid, *_: checkid in all_checks)
            db_filter_standards(cur, versionid, lambda standardid, *_: standardid in all_standards)
        db_filter_versions(cur, scopeid, lambda versionid, *_: versionid in all_versions)
        conn.commit()


def import_cert_yaml_dir(yaml_path, conn):
    for fn in sorted(os.listdir(yaml_path)):
        if fn.startswith('scs-') and fn.endswith('.yaml'):
            import_cert_yaml(os.path.join(yaml_path, fn), conn)


async def auth(request: Request, conn: Annotated[psycopg2.extensions.connection, Depends(get_conn)]):
    return get_current_account(await security(request), conn)


async def optional_auth(request: Request, conn: Annotated[psycopg2.extensions.connection, Depends(get_conn)]):
    return get_current_account(await optional_security(request), conn)


def check_role(
    account: Optional[tuple[str, str]],
    subject: str = None,
    roles: int = 0
):
    if account is None:
        raise HTTPException(status_code=401, detail="Permission denied")
    current_subject, present_roles = account
    if subject != current_subject and roles & present_roles != roles:
        raise HTTPException(status_code=401, detail="Permission denied")
    return current_subject


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/reports")
async def get_reports(
    account: Annotated[tuple[str, str], Depends(auth)],
    conn: Annotated[psycopg2.extensions.connection, Depends(get_conn)],
    subject: Optional[str] = None, limit: int = 10, skip: int = 0,
):
    if subject is None:
        subject, _ = account
    else:
        check_role(account, subject, ROLES['read_any'])
    with conn.cursor() as cur:
        return db_get_reports(cur, subject, limit, skip)


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
    account: Annotated[tuple[str, str], Depends(auth)],
    conn: Annotated[psycopg2.extensions.connection, Depends(get_conn)],
):
    content_type = request.headers['content-type']
    if content_type not in ('application/yaml', 'application/json'):
        raise HTTPException(status_code=500, detail="Unsupported content type")
    body = await request.body()
    body_text = body.decode("utf-8")
    sep = body_text.find(SEP)
    if sep < 0:
        raise HTTPException(status_code=401)
    sep += len(SEP)
    signature = body_text[:sep - 1]  # do away with the ampersand!
    body_text = body_text[sep:]
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
    check_role(account, subject, ROLES['append_any'])
    with conn.cursor() as cur:
        keys = db_get_keys(cur, subject)
    try:
        ssh_validate(keys, signature, body_text)
    except ValueError:
        raise HTTPException(status_code=401)
    expiration_lookup = {
        period: add_period(checked_at, period)
        for period in ('day', 'week', 'month', 'quarter')
    }
    expiration_lookup[None] = expiration_lookup['day']  # default
    scopeuuid = document['spec']['uuid']
    with conn.cursor() as cur:
        scopeid = db_get_scopeid(cur, scopeuuid)
        try:
            reportid = db_insert_report(cur, uuid, checked_at, subject, json_text, content_type, body)
        except UniqueViolation:
            raise HTTPException(status_code=409, detail="Conflict: report already present")
        invocation_ids = {}
        for invocation, idata in rundata['invocations'].items():
            invocationid = db_insert_invocation(cur, reportid, invocation, idata)
            invocation_ids[invocation] = invocationid
        for version, vdata in document['versions'].items():
            versionid = db_get_versionid(cur, scopeid, version)
            for check, rdata in vdata.items():
                checkid, lifetime = db_get_checkdata(cur, versionid, check)
                expiration = expiration_lookup[lifetime]
                invocationid = invocation_ids[rdata['invocation']]
                result = rdata['result']
                approval = 1 == result  # pre-approve good result
                db_insert_result(cur, reportid, invocationid, checkid, result, approval, expiration)
    conn.commit()


@app.get("/status/{subject}")
async def get_status(
    request: Request,
    account: Annotated[Optional[tuple[str, str]], Depends(optional_auth)],
    conn: Annotated[psycopg2.extensions.connection, Depends(get_conn)],
    subject: str,
    scopeuuid: str = None, version: str = None,
    privileged_view: bool = False,
):
    # note: text/html will be the default, but let's start with json to get the logic right
    accept = request.headers['accept']
    if 'application/json' not in accept and '*/*' not in accept:
        raise HTTPException(status_code=500, detail="client needs to accept application/json")
    if privileged_view:
        check_role(account, subject, ROLES['read_any'])
    with conn.cursor() as cur:
        rows = db_get_relevant_results(
            cur, subject, scopeuuid, version,
            approved_only=not privileged_view,
            grace_period_days=None if privileged_view else GRACE_PERIOD_DAYS,
        )
    # collect pass, DNF, fail per scope/version
    num_pass, num_dnf, num_fail = defaultdict(set), defaultdict(set), defaultdict(set)
    scopes = {}  # also collect some ancillary information
    for scopeuuid, scope, version, condition, check, ccondition, result in rows:
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
    account: Annotated[tuple[str, str], Depends(auth)],
    conn: Annotated[psycopg2.extensions.connection, Depends(get_conn)],
    approved: Optional[bool] = None, limit: int = 10, skip: int = 0,
):
    """get recent results, potentially filtered by approval status"""
    current_subject, roles = account
    if ROLES['read_any'] & roles == 0:
        raise HTTPException(status_code=401, detail="Permission denied")
    with conn.cursor() as cur:
        return db_get_recent_results(cur, approved, limit, skip)


@app.post("/results")
async def post_results(
    request: Request,
    account: Annotated[tuple[str, str], Depends(auth)],
    conn: Annotated[psycopg2.extensions.connection, Depends(get_conn)],
):
    """post approvals to this endpoint"""
    content_type = request.headers['content-type']
    if content_type not in ('application/json', ):
        raise HTTPException(status_code=500, detail="Unsupported content type")
    body = await request.body()
    document = json.loads(body.decode("utf-8"))
    records = [document] if isinstance(document, dict) else document
    current_subject, roles = account
    if ROLES['approve'] & roles == 0:
        raise HTTPException(status_code=401, detail="Permission denied")
    with conn.cursor() as cur:
        for record in records:
            db_patch_approval(cur, record)
    conn.commit()


if __name__ == "__main__":
    with mk_conn(settings=settings) as conn:
        with conn.cursor() as cur:
            db_ensure_schema(cur)
        del cur
        import_bootstrap(settings.bootstrap_path, conn=conn)
        import_cert_yaml_dir(settings.yaml_path, conn=conn)
    uvicorn.run(app, port=8080, log_level="info", workers=1)
