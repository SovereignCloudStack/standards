#!/usr/bin/env python3
from collections import defaultdict
from datetime import date, datetime, timedelta
import json
import os
import os.path
from shutil import which
from subprocess import run
from tempfile import NamedTemporaryFile
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext
import psycopg2
from psycopg2.errors import UniqueViolation
from psycopg2.extensions import connection
import ruamel.yaml
import uvicorn

from sql import (
    db_find_account, db_update_account, db_update_publickey, db_filter_publickeys, db_update_scope,
    db_update_version, db_update_standard, db_update_check, db_filter_checks, db_filter_standards,
    db_filter_versions, db_get_reports, db_get_keys, db_get_scopeid, db_insert_report, db_insert_invocation,
    db_get_versionid, db_get_checkdata, db_insert_result, db_get_relevant_results, db_get_recent_results,
    db_patch_approval, db_ensure_schema, db_get_apikeys, db_update_apikey, db_filter_apikeys,
)


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
# see https://passlib.readthedocs.io/en/stable/narr/quickstart.html
cryptctx = CryptContext(
    schemes=('argon2', 'bcrypt'),
    deprecated='auto',
)


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


def get_current_account(credentials: Optional[HTTPBasicCredentials], conn: connection):
    if credentials is None:
        return
    try:
        with conn.cursor() as cur:
            roles = db_find_account(cur, credentials.username)
            api_keys = db_get_apikeys(cur, credentials.username)
        match = False
        for keyhash in api_keys:
            # be sure to check every single one to make timing attacks less likely
            match = cryptctx.verify(credentials.password, keyhash) or match
        if not match:
            raise RuntimeError
        return credentials.username, roles
    except (KeyError, RuntimeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": f"Basic {security.realm}"},
        )


def import_bootstrap(bootstrap_path, conn):
    ryaml = ruamel.yaml.YAML(typ='safe')
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
            accountid = db_update_account(cur, {'subject': account['subject'], 'roles': roles})
            keyids = set(db_update_apikey(cur, accountid, h) for h in account.get("api_keys", ()))
            db_filter_apikeys(cur, accountid, lambda keyid, *_: keyid in keyids)
            keyids = set(db_update_publickey(cur, accountid, key) for key in account.get("keys", ()))
            db_filter_publickeys(cur, accountid, lambda keyid, *_: keyid in keyids)
        conn.commit()


def import_cert_yaml(yaml_path, conn):
    yaml = ruamel.yaml.YAML(typ='safe')
    with open(yaml_path, "r") as fileobj:
        document = yaml.load(fileobj.read())
    # The following will also delete entries that are not present in the given yaml.
    # It is paramount that all extant primary keys be kept because the reports refer to them, and
    # deletions will cascade! But we should only ever delete entries for non-stable versions; stable versions
    # are deemed immutable except maybe for checks, and for those, at least the ids are immutable.
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


async def auth(request: Request, conn: Annotated[connection, Depends(get_conn)]):
    return get_current_account(await security(request), conn)


async def optional_auth(request: Request, conn: Annotated[connection, Depends(get_conn)]):
    return get_current_account(await optional_security(request), conn)


def check_role(account: Optional[tuple[str, str]], subject: str = None, roles: int = 0):
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
    conn: Annotated[connection, Depends(get_conn)],
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
    conn: Annotated[connection, Depends(get_conn)],
):
    # TODO this endpoint handles almost all user input, so check thoroughly and generate nice errors!
    # check_role call further below because we need the subject from the document
    # (we could expect the subject in the path or query and then later only check equality)
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
    default_expiration = expiration_lookup['day']
    scopeuuid = document['spec']['uuid']
    with conn.cursor() as cur:
        try:
            scopeid = db_get_scopeid(cur, scopeuuid)
        except KeyError:
            raise HTTPException(status_code=500, detail=f"Unknown scope: {scopeuuid}")
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
                expiration = expiration_lookup.get(lifetime, default_expiration)
                invocationid = invocation_ids[rdata['invocation']]
                result = rdata['result']
                approval = 1 == result  # pre-approve good result
                db_insert_result(cur, reportid, invocationid, checkid, result, approval, expiration)
    conn.commit()


@app.get("/status/{subject}")
async def get_status(
    request: Request,
    account: Annotated[Optional[tuple[str, str]], Depends(optional_auth)],
    conn: Annotated[connection, Depends(get_conn)],
    subject: str,
    scopeuuid: str = None, version: str = None,
    privileged_view: bool = False,
):
    if privileged_view:
        check_role(account, subject, ROLES['read_any'])
    # note: text/html will be the default, but let's start with json to get the logic right
    accept = request.headers['accept']
    if 'application/json' not in accept and '*/*' not in accept:
        raise HTTPException(status_code=500, detail="client needs to accept application/json")
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
    conn: Annotated[connection, Depends(get_conn)],
    approved: Optional[bool] = None, limit: int = 10, skip: int = 0,
):
    """get recent results, potentially filtered by approval status"""
    check_role(account, roles=ROLES['read_any'])
    with conn.cursor() as cur:
        return db_get_recent_results(cur, approved, limit, skip, grace_period_days=GRACE_PERIOD_DAYS)


@app.post("/results")
async def post_results(
    request: Request,
    account: Annotated[tuple[str, str], Depends(auth)],
    conn: Annotated[connection, Depends(get_conn)],
):
    """post approvals to this endpoint"""
    check_role(account, roles=ROLES['approve'])
    content_type = request.headers['content-type']
    if content_type not in ('application/json', ):
        raise HTTPException(status_code=500, detail="Unsupported content type")
    body = await request.body()
    document = json.loads(body.decode("utf-8"))
    records = [document] if isinstance(document, dict) else document
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
