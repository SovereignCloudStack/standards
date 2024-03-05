#!/usr/bin/env python3
import os
import os.path

from fastapi import Depends, FastAPI
import psycopg2
import ruamel.yaml
import uvicorn


class Settings:
    def __init__(self):
        self.db_host = os.getenv("SCM_DB_HOST", "localhost")
        self.db_user = os.getenv("SCM_DB_USER", "postgres")
        self.db_password = os.getenv("SCM_DB_PASSWORD", "mysecretpassword")
        self.bootstrap_path = os.path.abspath("./bootstrap.yaml")


ROLES = {'read_any': 1, 'append_any': 2, 'admin': 4}


# do I hate these globals, but I don't see another way with these frameworks
app = FastAPI()
settings = Settings()


def mk_conn(settings=settings):
    return psycopg2.connect(host=settings.db_host, user=settings.db_user, password=settings.db_password)


def get_conn(settings=settings):
    conn = mk_conn(settings=settings)
    try:
        yield conn
    finally:
        conn.close()


def ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS account (
                subject varchar PRIMARY KEY,
                apikey varchar,
                publickey varchar,
                roles int
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
async def root(db: psycopg2.extensions.connection = Depends(get_conn)):
    return {"message": "Hello World"}


if __name__ == "__main__":
    with mk_conn(settings=settings) as conn:
        ensure_schema(conn=conn)
        import_bootstrap(settings.bootstrap_path, conn=conn)
    uvicorn.run(app, port=8080, log_level="info", workers=1)
