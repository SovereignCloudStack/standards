#!/usr/bin/env python3
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


ROLES = {'read_any': 1, 'append_any': 2, 'admin': 4}
WINDOW = timedelta(weeks=1)


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
    with conn.cursor() as cur:
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS account (
                subject text PRIMARY KEY,
                apikey text,
                publickey text,
                roles integer
            );
            CREATE TABLE IF NOT EXISTS report (
                reportid SERIAL PRIMARY KEY,
                uuid text UNIQUE,
                checked_at timestamp,
                subject text,
                scope text,
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
                id SERIAL PRIMARY KEY,
                version text,
                "check" text,
                result int,
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
    scope = document['spec']['name'].strip().replace('  ', ' ').lower().replace(' ', '-')
    with conn.cursor() as cur:
        try:
            cur.execute(
                '''
                INSERT INTO report (uuid, checked_at, subject, scope, data, rawformat, raw)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING reportid;
                ''',
                (uuid, checked_at, subject, scope, json_text, content_type, body),
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
            for check, rdata in vdata.items():
                invocationid = invocation_ids[rdata['invocation']]
                cur.execute(
                    '''
                    INSERT INTO result (reportid, invocationid, version, "check", result)
                    VALUES (%s, %s, %s, %s, %s);
                    ''',
                    (reportid, invocationid, version, check, rdata['result']),
                )
    conn.commit()


@app.get("/status/{subject}")
async def get_status(
    request: Request,
    subject: str,
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
        # fetch results for all versions within the relevant timeframe
        cur.execute(
            '''
            SELECT scope, version, "check", result
            FROM result NATURAL JOIN report
            WHERE subject = %s AND checked_at >= %s;
            ''',
            (subject, datetime.now() - WINDOW),
        )
        return [row for row in cur.fetchall()]


if __name__ == "__main__":
    with mk_conn(settings=settings) as conn:
        ensure_schema(conn=conn)
        import_bootstrap(settings.bootstrap_path, conn=conn)
    uvicorn.run(app, port=8080, log_level="info", workers=1)
