#!/usr/bin/env python3
from collections import defaultdict
from datetime import date, datetime, timedelta
import json
import os
import os.path
from shutil import which
from subprocess import run
from tempfile import NamedTemporaryFile
# _thread: low-level library, but (contrary to the name) not private
# https://docs.python.org/3/library/_thread.html
from _thread import allocate_lock, get_ident
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from jinja2 import Environment
from passlib.context import CryptContext
import psycopg2
from psycopg2.errors import UniqueViolation
from psycopg2.extensions import connection
import ruamel.yaml
import uvicorn

from sql import (
    db_find_account, db_update_account, db_update_publickey, db_filter_publickeys, db_get_reports,
    db_get_keys, db_insert_report, db_get_recent_results2, db_patch_approval2,
    db_ensure_schema, db_get_apikeys, db_update_apikey, db_filter_apikeys,
    db_patch_subject, db_get_subjects, db_insert_result2, db_get_relevant_results2,
)


try:
    from scs_cert_lib import load_spec, annotate_validity, compile_suite
except ImportError:
    # the following course of action is not unproblematic because the Tests directory will be
    # mounted to the Docker instance, hence it's hard to tell what version we are gonna get;
    # however, unlike the reloading of the config, the import only happens once, and at that point
    # in time, both monitor.py and scs_cert_lib.py should come from the same git checkout
    import sys; sys.path.insert(0, os.path.abspath('../Tests'))  # noqa: E702
    from scs_cert_lib import load_spec, annotate_validity, compile_suite


class Settings:
    def __init__(self):
        self.db_host = os.getenv("SCM_DB_HOST", "localhost")
        self.db_user = os.getenv("SCM_DB_USER", "postgres")
        password_file_path = os.getenv("SCM_DB_PASSWORD_FILE", None)
        if password_file_path:
            with open(os.path.abspath(password_file_path), "r") as fileobj:
                self.db_password = fileobj.read().strip()
        else:
            self.db_password = os.getenv("SCM_DB_PASSWORD", "mysecretpassword")
        self.bootstrap_path = os.path.abspath("./bootstrap.yaml")
        self.template_path = os.path.abspath("./templates")
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
TEMPLATE_OVERVIEW = 'overview.html'
TEMPLATE_OVERVIEW_FRAGMENT = 'overview_fragment.html'
TEMPLATE_OVERVIEW_MD = 'overview.md'
REQUIRED_TEMPLATES = (TEMPLATE_OVERVIEW, TEMPLATE_OVERVIEW_FRAGMENT, TEMPLATE_OVERVIEW_MD)


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
env = Environment()  # populate this on startup (final section of this file)
templates_map = {
    k: None for k in REQUIRED_TEMPLATES
}
# map thread id (cf. `get_ident`) to a dict that maps scope uuids to scope documents
# -- access this using function `get_scopes`
_scopes = defaultdict(dict)  # thread-local storage (similar to threading.local, but more efficient)
_scopes_lock = allocate_lock()  # mutex lock so threads can add their local storage without races


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


def get_current_account(
    credentials: Optional[HTTPBasicCredentials],
    conn: connection,
) -> Optional[tuple[str, str]]:
    """Extract account info from `credentials`.

    Returns `None` if unauthorized, otherwise a tuple `(current_subject, present_roles)`.
    """
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
    accounts = data.get('accounts', ())
    subjects = data.get('subjects', {})
    if not accounts and not subjects:
        return
    with conn.cursor() as cur:
        for account in accounts:
            roles = sum(ROLES[r] for r in account.get('roles', ()))
            accountid = db_update_account(cur, {'subject': account['subject'], 'roles': roles})
            keyids = set(db_update_apikey(cur, accountid, h) for h in account.get("api_keys", ()))
            db_filter_apikeys(cur, accountid, lambda keyid, *_: keyid in keyids)
            keyids = set(db_update_publickey(cur, accountid, key) for key in account.get("keys", ()))
            db_filter_publickeys(cur, accountid, lambda keyid, *_: keyid in keyids)
        for subject, record in subjects.items():
            db_patch_subject(cur, {'subject': subject, **record})
        conn.commit()


def precompute_targets(version):
    suite = compile_suite(f"{version['version']}", version['include'])
    return {
        'suite': suite,
        'targets': {
            tname: suite.select(tname, target_spec)
            for tname, target_spec in version['targets'].items()
        }
    }


def import_cert_yaml(yaml_path, target_dict):
    yaml = ruamel.yaml.YAML(typ='safe')
    with open(yaml_path, "r") as fileobj:
        spec = load_spec(yaml.load(fileobj.read()))
    annotate_validity(spec['timeline'], spec['versions'], date.today())
    target_dict[spec['uuid']] = {
        'spec': spec,
        'versions': {
            version['version']: precompute_targets(version)
            for version in spec['versions'].values()
        }
    }


def import_cert_yaml_dir(yaml_path, target_dict):
    for fn in sorted(os.listdir(yaml_path)):
        if fn.startswith('scs-') and fn.endswith('.yaml'):
            import_cert_yaml(os.path.join(yaml_path, fn), target_dict)


def get_scopes():
    """returns thread-local copy of the scopes dict"""
    ident = get_ident()
    with _scopes_lock:
        yaml_path = _scopes['_yaml_path']
        counter = _scopes['_counter']
        current = _scopes.get(ident)
        if current is None:
            _scopes[ident] = current = {'_counter': -1}
    if current['_counter'] != counter:
        import_cert_yaml_dir(yaml_path, current)
        current['_counter'] = counter
    return current


def import_templates(template_dir, env, templates):
    for fn in os.listdir(template_dir):
        if fn.startswith("."):
            continue
        name = fn.removesuffix('.j2')
        if name not in templates:
            continue
        with open(os.path.join(template_dir, fn), "r") as fileobj:
            templates[name] = env.from_string(fileobj.read())


def validate_templates(templates, required_templates=REQUIRED_TEMPLATES):
    missing = [key for key in required_templates if not templates.get(key)]
    if missing:
        raise RuntimeError(f"missing templates: {', '.join(missing)}")


async def auth(request: Request, conn: Annotated[connection, Depends(get_conn)]):
    return get_current_account(await security(request), conn)


async def optional_auth(request: Request, conn: Annotated[connection, Depends(get_conn)]):
    return get_current_account(await optional_security(request), conn)


def check_role(account: Optional[tuple[str, str]], subject: str = None, roles: int = 0):
    """Raise an HTTPException with code 401 if `account` has insufficient permissions.

    The `account` is expected as returned by `get_current_account` -- either `None` if unauthorized, or
    a tuple `(current_subject, present_roles)`.

    Here, we assume that the account has full access to its own data, i.e., if `account[0] == subject`.
    Otherwise, the account must at least have the roles given, i.e., `roles & account[1] == roles`.
    """
    if account is None:
        raise HTTPException(status_code=401, detail="Permission denied")
    current_subject, present_roles = account
    if subject != current_subject and roles & present_roles != roles:
        raise HTTPException(status_code=401, detail="Permission denied")
    return current_subject


@app.get("/")
async def root():
    # we might use the following redirect in the future:
    # return RedirectResponse("/pages")
    # but keep this silly message for the time being, so as not to expose the work in progress too much
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
    if content_type not in ('application/x-signed-yaml', 'application/x-signed-json'):
        # see https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/415
        raise HTTPException(status_code=415, detail="Unsupported Media Type")
    body = await request.body()
    body_text = body.decode("utf-8")
    sep = body_text.find(SEP)
    if sep < 0:
        raise HTTPException(status_code=401)
    sep += len(SEP)
    signature = body_text[:sep - 1]  # do away with the ampersand!
    body_text = body_text[sep:]
    json_text = None
    if content_type.endswith('-yaml'):
        yaml = ruamel.yaml.YAML(typ='safe')
        document = yaml.load(body_text)
        json_text = json.dumps(document, cls=TimestampEncoder)
    elif content_type.endswith("-json"):
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
    scopeuuid = document['spec']['uuid']
    with conn.cursor() as cur:
        try:
            reportid = db_insert_report(cur, uuid, checked_at, subject, json_text, content_type, body)
        except UniqueViolation:
            raise HTTPException(status_code=409, detail="Conflict: report already present")
        for version, vdata in document['versions'].items():
            for check, rdata in vdata.items():
                result = rdata['result']
                approval = 1 == result  # pre-approve good result
                db_insert_result2(cur, checked_at, subject, scopeuuid, version, check, result, approval, reportid)
    conn.commit()


def convert_result_rows_to_dict2(rows, scopes_lookup, grace_period_days):
    # collect result per subject/scope/version
    by_context = defaultdict(dict)
    scopes = set()  # also collect some ancillary information
    subjects = set()
    for subject, scopeuuid, version, testcase, result, checked_at in rows:
        scopes.add(scopeuuid)
        subjects.add(subject)
        by_context[(subject, scopeuuid, version)][testcase] = {'result': result, 'checked_at': checked_at}
    results = defaultdict(dict)
    for subject in subjects:
        for scopeuuid in scopes:
            results[subject][scopeuuid] = {"versions": defaultdict(dict), "result": 0}
    now = datetime.now()
    if grace_period_days:
        now -= timedelta(days=grace_period_days)
    for context, scenario_results in by_context.items():
        subject, scopeuuid, version = context
        precomputed = scopes_lookup.get(scopeuuid)
        if precomputed is None:
            continue
        validity = precomputed['spec']['versions'][version]['validity']
        main_suite = precomputed['versions'][version]['targets']['main']
        by_result = main_suite.evaluate(scenario_results, now=now)
        missing, failed = by_result[0], by_result[-1]
        total_result = -1 if failed else 0 if missing else 1
        results[subject][scopeuuid]["versions"][version] = {'result': total_result, 'validity': validity}
        if total_result == 1 and validity in ('effective', 'warn'):
            results[subject][scopeuuid]["result"] = 1
    return results


@app.get("/status")
async def get_status(
    request: Request,
    account: Annotated[Optional[tuple[str, str]], Depends(optional_auth)],
    conn: Annotated[connection, Depends(get_conn)],
    subject: str = None,
    scopeuuid: str = None, version: str = None,
    privileged_view: bool = False,
):
    if privileged_view:
        check_role(account, subject, ROLES['read_any'])
    # note: text/html will be the default, but let's start with json to get the logic right
    accept = request.headers['accept']
    if 'application/json' not in accept and '*/*' not in accept:
        # see https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/406
        raise HTTPException(status_code=406, detail="client needs to accept application/json")
    with conn.cursor() as cur:
        rows2 = db_get_relevant_results2(
            cur, subject, scopeuuid, version,
            approved_only=not privileged_view,
        )
    grace_period_days = None if privileged_view else GRACE_PERIOD_DAYS
    return convert_result_rows_to_dict2(rows2, get_scopes(), grace_period_days=grace_period_days)


@app.get("/table")
async def get_table(
    request: Request,
    account: Annotated[Optional[tuple[str, str]], Depends(optional_auth)],
    conn: Annotated[connection, Depends(get_conn)],
):
    with conn.cursor() as cur:
        rows2 = db_get_relevant_results2(cur, approved_only=True)
    results2 = convert_result_rows_to_dict2(rows2, get_scopes(), grace_period_days=GRACE_PERIOD_DAYS)
    result = templates_map[TEMPLATE_OVERVIEW_MD].render(results=results2)
    return Response(
        content=result,
        media_type='text/markdown',
    )


@app.get("/pages")
async def get_pages(
    request: Request,
    account: Annotated[Optional[tuple[str, str]], Depends(optional_auth)],
    conn: Annotated[connection, Depends(get_conn)],
    part: str = "full",
):
    with conn.cursor() as cur:
        rows2 = db_get_relevant_results2(cur, approved_only=True)
    results2 = convert_result_rows_to_dict2(rows2, get_scopes(), grace_period_days=GRACE_PERIOD_DAYS)
    result = templates_map[TEMPLATE_OVERVIEW_FRAGMENT].render(results=results2)
    if part == "full":
        result = templates_map[TEMPLATE_OVERVIEW].render(fragment=result)
    return Response(
        content=result,
        media_type='text/html',
    )


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
        return db_get_recent_results2(cur, approved, limit, skip, max_age_days=GRACE_PERIOD_DAYS)


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
            db_patch_approval2(cur, record)
    conn.commit()


@app.get("/subjects")
async def get_subjects(
    request: Request,
    account: Annotated[tuple[str, str], Depends(auth)],
    conn: Annotated[connection, Depends(get_conn)],
    active: Optional[bool] = None, limit: int = 10, skip: int = 0,
):
    """get subjects, potentially filtered by activity status"""
    check_role(account, roles=ROLES['read_any'])
    with conn.cursor() as cur:
        return db_get_subjects(cur, active, limit, skip)


@app.post("/subjects")
async def post_subjects(
    request: Request,
    account: Annotated[tuple[str, str], Depends(auth)],
    conn: Annotated[connection, Depends(get_conn)],
):
    """post approvals to this endpoint"""
    check_role(account, roles=ROLES['admin'])
    content_type = request.headers['content-type']
    if content_type not in ('application/json', ):
        raise HTTPException(status_code=500, detail="Unsupported content type")
    body = await request.body()
    document = json.loads(body.decode("utf-8"))
    records = [document] if isinstance(document, dict) else document
    with conn.cursor() as cur:
        for record in records:
            db_patch_subject(cur, record)
    conn.commit()


def passed_filter(scopedata):
    if not scopedata or not scopedata.get('versions'):
        return ""
    # sort passed versions into buckets according to validity status
    buckets = defaultdict(list)
    for vname, val in scopedata['versions'].items():
        if val['result'] != 1:
            continue
        buckets[val['validity']].append(vname)
    # only show "warn" versions if no effective ones are passed
    passed = buckets['effective'] or [vname + '†' for vname in buckets['warn']]
    # append draft versions
    passed.extend([vname + '*' for vname in buckets['draft']])
    return ", ".join(passed)


if __name__ == "__main__":
    env.filters.update(passed=passed_filter)
    with mk_conn(settings=settings) as conn:
        db_ensure_schema(conn)
        import_bootstrap(settings.bootstrap_path, conn=conn)
        _scopes.update({
            '_yaml_path': settings.yaml_path,
            '_counter': 0,
        })
        _ = get_scopes()  # make sure they can be read
        import_templates(settings.template_path, env=env, templates=templates_map)
        validate_templates(templates=templates_map)
    uvicorn.run(app, host='0.0.0.0', port=8080, log_level="info", workers=1)
