#!/usr/bin/env python3
from collections import defaultdict
from datetime import date, datetime, timedelta
from enum import Enum
import json
import logging
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
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from jinja2 import Environment
from markdown import markdown
from passlib.context import CryptContext
import psycopg2
from psycopg2.errors import UniqueViolation
from psycopg2.extensions import connection
import ruamel.yaml
import uvicorn

from sql import (
    db_find_account, db_update_account, db_update_publickey, db_filter_publickeys, db_get_reports,
    db_get_keys, db_insert_report, db_get_recent_results2, db_patch_approval2, db_get_report,
    db_ensure_schema, db_get_apikeys, db_update_apikey, db_filter_apikeys, db_clear_delegates,
    db_patch_subject, db_get_subjects, db_insert_result2, db_get_relevant_results2, db_add_delegate,
    db_find_subjects,
)


logger = logging.getLogger(__name__)


try:
    from scs_cert_lib import load_spec, annotate_validity, compile_suite, add_period
except ImportError:
    # the following course of action is not unproblematic because the Tests directory will be
    # mounted to the Docker instance, hence it's hard to tell what version we are gonna get;
    # however, unlike the reloading of the config, the import only happens once, and at that point
    # in time, both monitor.py and scs_cert_lib.py should come from the same git checkout
    import sys; sys.path.insert(0, os.path.abspath('../Tests'))  # noqa: E702
    from scs_cert_lib import load_spec, annotate_validity, compile_suite, add_period


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
        self.base_url = os.getenv("SCM_BASE_URL", '/')
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
ASTERISK_LOOKUP = {'effective': '', 'draft': '*', 'warn': '†', 'deprecated': '††'}


class ViewType(Enum):
    markdown = "markdown"
    page = "page"
    fragment = "fragment"


VIEW_DETAIL = {
    ViewType.markdown: 'details.md',
    ViewType.fragment: 'details.md',
    ViewType.page: 'overview.html',
}
VIEW_TABLE = {
    ViewType.markdown: 'overview.md',
    ViewType.fragment: 'overview.md',
    ViewType.page: 'overview.html',
}
REQUIRED_TEMPLATES = tuple(set(fn for view in (VIEW_DETAIL, VIEW_TABLE) for fn in view.values()))


# do I hate these globals, but I don't see another way with these frameworks
app = FastAPI()
security = HTTPBasic(realm="Compliance monitor", auto_error=True)  # use False for optional login
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
            db_clear_delegates(cur, accountid)
            for delegate in account.get('delegates', ()):
                db_add_delegate(cur, accountid, delegate)
            keyids = set(db_update_apikey(cur, accountid, h) for h in account.get("api_keys", ()))
            db_filter_apikeys(cur, accountid, lambda keyid, *_: keyid in keyids)
            keyids = set(db_update_publickey(cur, accountid, key) for key in account.get("keys", ()))
            db_filter_publickeys(cur, accountid, lambda keyid, *_: keyid in keyids)
        for subject, record in subjects.items():
            db_patch_subject(cur, {'subject': subject, **record})
        conn.commit()


class PrecomputedVersion:
    """Precompute all `TestSuite` instances necessary to evaluate the results of some version"""
    def __init__(self, version):
        self.name = version['version']
        self.suite = compile_suite(self.name, version['include'])
        self.validity = version['validity']
        self.listed = bool(version['_explicit_validity'])
        self.targets = {
            tname: self.suite.select(tname, target_spec)
            for tname, target_spec in version['targets'].items()
        }

    def evaluate(self, scenario_results):
        """evaluate the results for this version and return the canonical JSON output"""
        target_results = {}
        for tname, suite in self.targets.items():
            target_results[tname] = {
                'testcases': [testcase['id'] for testcase in suite.testcases],
                'result': suite.evaluate(scenario_results),
            }
        return {
            'testcases': {tc['id']: tc for tc in self.suite.testcases},
            'results': scenario_results,
            'result': target_results['main']['result'],
            'targets': target_results,
            'validity': self.validity,
        }


class PrecomputedScope:
    """Precompute all `TestSuite` instances necessary to evaluate the results of some scope"""
    def __init__(self, spec):
        self.name = spec['name']
        self.spec = spec
        self.versions = {
            version['version']: PrecomputedVersion(version)
            for version in spec['versions'].values()
        }

    def evaluate(self, scope_results):
        """evaluate the results for this scope and return the canonical JSON output"""
        version_results = {
            vname: self.versions[vname].evaluate(scenario_results)
            for vname, scenario_results in scope_results.items()
        }
        by_validity = defaultdict(list)
        for vname in scope_results:
            by_validity[self.versions[vname].validity].append(vname)
        # go through worsening validity values until a passing version is found
        relevant = []
        for validity in ('effective', 'warn', 'deprecated'):
            vnames = by_validity[validity]
            relevant.extend(vnames)
            if any(version_results[vname]['result'] == 1 for vname in vnames):
                break
        # always include draft (but only at the end)
        relevant.extend(by_validity['draft'])
        passed = [vname for vname in relevant if version_results[vname]['result'] == 1]
        return {
            'name': self.name,
            'versions': version_results,
            'relevant': relevant,
            'passed': passed,
            'passed_str': ', '.join([
                vname + ASTERISK_LOOKUP[self.versions[vname].validity]
                for vname in passed
            ]),
        }

    def update_lookup(self, target_dict):
        """Create entries in a lookup mapping for each testcase that occurs in this scope.

        This mapping from triples (scope uuid, version name, testcase id) to testcase facilitates
        evaluating result sets from database queries a great deal, because then just one lookup operation
        tells us whether a result row can be associated with any known testcase, and if so, whether the
        result is still valid (looking at the testcase's lifetime).

        In the future, the mapping could even be simplified by deriving a unique id from each triple that
        could then be stored (redundantly) in a dedicated database column, and the mapping could be from
        just one id (instead of a triple) to testcase.
        """
        scope_uuid = self.spec['uuid']
        for vname, precomputed_version in self.versions.items():
            listed = precomputed_version.listed
            for testcase in precomputed_version.suite.testcases:
                # put False if listed is False, else put testcase
                target_dict[(scope_uuid, vname, testcase['id'])] = listed and testcase


def import_cert_yaml(yaml_path, target_dict):
    yaml = ruamel.yaml.YAML(typ='safe')
    with open(yaml_path, "r") as fileobj:
        spec = load_spec(yaml.load(fileobj.read()))
    annotate_validity(spec['timeline'], spec['versions'], date.today())
    target_dict[spec['uuid']] = precomputed_scope = PrecomputedScope(spec)
    precomputed_scope.update_lookup(target_dict)


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
        current.clear()
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


@app.get("/reports/{report_uuid}")
async def get_report(
    account: Annotated[tuple[str, str], Depends(auth)],
    conn: Annotated[connection, Depends(get_conn)],
    report_uuid: str,
):
    with conn.cursor() as cur:
        specs = db_get_report(cur, report_uuid)
    if not specs:
        raise HTTPException(status_code=404)
    spec = specs[0]
    check_role(account, spec['subject'], ROLES['read_any'])
    return Response(content=json.dumps(spec, indent=2), media_type="application/json")


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

    auth_subject, _ = account
    with conn.cursor() as cur:
        keys = db_get_keys(cur, auth_subject)
        delegation_subjects = db_find_subjects(cur, auth_subject)

    body = await request.body()
    body_text = body.decode("utf-8")
    sep = body_text.find(SEP)
    if sep < 0:
        raise HTTPException(status_code=401, detail="missing signature")
    sep += len(SEP)
    signature = body_text[:sep - 1]  # do away with the ampersand!
    body_text = body_text[sep:]
    try:
        ssh_validate(keys, signature, body_text)
    except Exception:
        raise HTTPException(status_code=401, detail="verification failed")

    json_texts = []
    if content_type.endswith('-yaml'):
        yaml = ruamel.yaml.YAML(typ='safe')
        documents = list(yaml.load_all(body_text))  # ruamel.yaml doesn't have API docs: this is a generator
        json_texts = [json.dumps(document, cls=TimestampEncoder) for document in documents]
    elif content_type.endswith("-json"):
        documents = [json.loads(body_text)]
        json_texts = [body_text]
    else:
        # unreachable due to the content-type check at the top
        raise AssertionError("branch should never be reached")

    if not documents:
        raise HTTPException(status_code=200, detail="empty reports")

    allowed_subjects = {auth_subject} | set(delegation_subjects)
    for document in documents:
        check_role(account, document['subject'], ROLES['append_any'])
        if document['subject'] not in allowed_subjects:
            raise HTTPException(status_code=401, detail="delegation problem?")

    with conn.cursor() as cur:
        for document, json_text in zip(documents, json_texts):
            rundata = document['run']
            uuid, subject, checked_at = rundata['uuid'], document['subject'], document['checked_at']
            scopeuuid = document['spec']['uuid']
            try:
                reportid = db_insert_report(cur, uuid, checked_at, subject, json_text)
            except UniqueViolation:
                raise HTTPException(status_code=409, detail="Conflict: report already present")
            for version, vdata in document['versions'].items():
                for check, rdata in vdata.items():
                    result = rdata['result']
                    approval = 1 == result  # pre-approve good result
                    db_insert_result2(cur, checked_at, subject, scopeuuid, version, check, result, approval, reportid)
    conn.commit()


def convert_result_rows_to_dict2(
    rows, scopes_lookup, grace_period_days=0, scopes=(), subjects=(), include_report=False,
):
    """evaluate all versions occurring in query result `rows`, returning canonical JSON representation"""
    now = datetime.now()
    if grace_period_days:
        now -= timedelta(days=grace_period_days)
    # collect result per subject/scope/version
    preliminary = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))  # subject -> scope -> version
    missing = set()
    for subject, scope_uuid, version, testcase_id, result, checked_at, report_uuid in rows:
        testcase = scopes_lookup.get((scope_uuid, version, testcase_id))
        if not testcase:
            # it can be False (testcase is known but version too old) or None (testcase not known)
            # only report the latter case
            if testcase is None:
                missing.add((scope_uuid, version, testcase_id))
            continue
        # drop value if too old
        expires_at = add_period(checked_at, testcase.get('lifetime'))
        if now >= expires_at:
            continue
        tc_result = dict(result=result, checked_at=checked_at)
        if include_report:
            tc_result.update(report=report_uuid)
        preliminary[subject][scope_uuid][version][testcase_id] = tc_result
    if missing:
        logger.warning('missing objects: ' + ', '.join(repr(x) for x in missing))
    # make sure the requested subjects and scopes are present (facilitates writing jinja2 templates)
    for subject in subjects:
        for scope in scopes:
            _ = preliminary[subject][scope]
    return {
        subject: {
            scope_uuid: scopes_lookup[scope_uuid].evaluate(scope_result)
            for scope_uuid, scope_result in subject_result.items()
        }
        for subject, subject_result in preliminary.items()
    }


@app.get("/status")
async def get_status(
    request: Request,
    account: Annotated[Optional[tuple[str, str]], Depends(auth)],
    conn: Annotated[connection, Depends(get_conn)],
    subject: str = None, scopeuuid: str = None, version: str = None,
):
    check_role(account, subject, ROLES['read_any'])
    # note: text/html will be the default, but let's start with json to get the logic right
    accept = request.headers['accept']
    if 'application/json' not in accept and '*/*' not in accept:
        # see https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/406
        raise HTTPException(status_code=406, detail="client needs to accept application/json")
    with conn.cursor() as cur:
        rows2 = db_get_relevant_results2(cur, subject, scopeuuid, version, approved_only=False)
    return convert_result_rows_to_dict2(rows2, get_scopes(), include_report=True)


def render_view(view, view_type, results, base_url='/', title=None):
    media_type = {ViewType.markdown: 'text/markdown'}.get(view_type, 'text/html')
    stage1 = stage2 = view[view_type]
    if view_type is ViewType.page:
        stage1 = view[ViewType.fragment]
    def detail_url(subject, scope): return f"{base_url}page/detail/{subject}/{scope}"  # noqa: E306,E704
    def report_url(report): return f"{base_url}reports/{report}"  # noqa: E306,E704
    fragment = templates_map[stage1].render(results=results, detail_url=detail_url, report_url=report_url)
    if view_type != ViewType.markdown and stage1.endswith('.md'):
        fragment = markdown(fragment, extensions=['extra'])
    if stage1 != stage2:
        fragment = templates_map[stage2].render(fragment=fragment, title=title)
    return Response(content=fragment, media_type=media_type)


@app.get("/{view_type}/detail/{subject}/{scopeuuid}")
async def get_detail(
    request: Request,
    conn: Annotated[connection, Depends(get_conn)],
    view_type: ViewType,
    subject: str,
    scopeuuid: str,
):
    with conn.cursor() as cur:
        rows2 = db_get_relevant_results2(cur, subject, scopeuuid, approved_only=True)
    results2 = convert_result_rows_to_dict2(
        rows2, get_scopes(), grace_period_days=GRACE_PERIOD_DAYS,
        subjects=(subject, ), scopes=(scopeuuid, ),
    )
    return render_view(VIEW_DETAIL, view_type, results2, base_url=settings.base_url, title=f'{subject} compliance')


@app.get("/{view_type}/detail_full/{subject}/{scopeuuid}")
async def get_detail_full(
    request: Request,
    account: Annotated[Optional[tuple[str, str]], Depends(auth)],
    conn: Annotated[connection, Depends(get_conn)],
    view_type: ViewType,
    subject: str,
    scopeuuid: str,
):
    check_role(account, subject, ROLES['read_any'])
    with conn.cursor() as cur:
        rows2 = db_get_relevant_results2(cur, subject, scopeuuid, approved_only=False)
    results2 = convert_result_rows_to_dict2(
        rows2, get_scopes(), include_report=True, subjects=(subject, ), scopes=(scopeuuid, ),
    )
    return render_view(VIEW_DETAIL, view_type, results2, base_url=settings.base_url, title=f'{subject} compliance')


@app.get("/{view_type}/table")
async def get_table(
    request: Request,
    conn: Annotated[connection, Depends(get_conn)],
    view_type: ViewType,
):
    with conn.cursor() as cur:
        rows2 = db_get_relevant_results2(cur, approved_only=True)
    results2 = convert_result_rows_to_dict2(rows2, get_scopes(), grace_period_days=GRACE_PERIOD_DAYS)
    return render_view(VIEW_TABLE, view_type, results2, base_url=settings.base_url, title="SCS compliance overview")


@app.get("/{view_type}/table_full")
async def get_table_full(
    request: Request,
    account: Annotated[Optional[tuple[str, str]], Depends(auth)],
    conn: Annotated[connection, Depends(get_conn)],
    view_type: ViewType,
):
    check_role(account, None, ROLES['read_any'])
    with conn.cursor() as cur:
        rows2 = db_get_relevant_results2(cur, approved_only=False)
    results2 = convert_result_rows_to_dict2(rows2, get_scopes())
    return render_view(VIEW_TABLE, view_type, results2, base_url=settings.base_url, title="SCS compliance overview")


@app.get("/pages")
async def get_pages(
    request: Request,
    conn: Annotated[connection, Depends(get_conn)],
):
    return RedirectResponse("/page/table")


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


def passed_filter(results, subject, scope):
    """Jinja filter to pick list of passed versions from `results` for given `subject` and `scope`"""
    subject_data = results.get(subject)
    if not subject_data:
        return ""
    scope_data = subject_data.get(scope)
    if not scope_data:
        return ""
    return scope_data['passed_str']


def verdict_filter(value):
    """Jinja filter to turn a canonical result value into a written verdict (PASS, MISS, or FAIL)"""
    # be fault-tolerant here and turn every non-canonical value into a MISS
    return {1: 'PASS', -1: 'FAIL'}.get(value, 'MISS')


def verdict_check_filter(value):
    """Jinja filter to turn a canonical result value into a symbolic verdict (✔, ⚠, or ✘)"""
    # be fault-tolerant here and turn every non-canonical value into a MISS
    return {1: '✔', -1: '✘'}.get(value, '⚠')


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    env.filters.update(
        passed=passed_filter,
        verdict=verdict_filter,
        verdict_check=verdict_check_filter,
        markdown=markdown,
    )
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
