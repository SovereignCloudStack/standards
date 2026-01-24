#!/usr/bin/env python3
# AN IMPORTANT NOTE ON CONCURRENCY:
# This server is based on uvicorn and, as such, is not multi-threaded.
# (It could use multiple processes, but we don't do that yet.)
# Consequently, we don't need to use any measures for thread-safety.
# However, if we do at some point enable the use of multiple processes,
# we should make sure that all processes are "on the same page" with regard
# to basic data such as certificate scopes, templates, and accounts.
# One way to achieve this synchronicity could be to use the Postgres server
# more, however, I hope that more efficient ways are possible.
# Also, it is quite likely that the signal SIGHUP could no longer be used
# to trigger a re-load. In any case, the `uvicorn.run` call would have to be
# fundamentally changed:
# > You must pass the application as an import string to enable 'reload' or 'workers'.
from collections import defaultdict
from datetime import date, datetime, timedelta
from enum import Enum
import json
import logging
import os
import os.path
from shutil import which
import signal
from subprocess import run
from tempfile import NamedTemporaryFile
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
    db_find_subjects, db_insert_result2, db_get_relevant_results2, db_add_delegate, db_get_group,
)


logger = logging.getLogger(__name__)


try:
    from scs_cert_lib import load_spec, annotate_validity, add_period, eval_buckets, evaluate
except ImportError:
    # the following course of action is not unproblematic because the Tests directory will be
    # mounted to the Docker instance, hence it's hard to tell what version we are gonna get;
    # however, unlike the reloading of the config, the import only happens once, and at that point
    # in time, both monitor.py and scs_cert_lib.py should come from the same git checkout
    import sys; sys.path.insert(0, os.path.abspath('../Tests'))  # noqa: E702
    from scs_cert_lib import load_spec, annotate_validity, add_period, eval_buckets, evaluate


class Settings:
    def __init__(self):
        self.db_host = os.getenv("SCM_DB_HOST", "localhost")
        self.db_port = os.getenv("SCM_DB_PORT", 5432)
        self.db_user = os.getenv("SCM_DB_USER", "postgres")
        # use default value of None for security reasons (won't be matched)
        self.hc_user = os.getenv("SCM_HC_USER", None)
        self.hc_password = os.getenv("SCM_HC_PASSWORD", None)
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


GROUP_PREFIX = 'group-'
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


VIEW_REPORT = {
    ViewType.markdown: 'report.md',
    ViewType.fragment: 'report.md',
    ViewType.page: 'overview.html',
}
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
VIEW_SCOPE = {
    ViewType.markdown: 'scope.md',
    ViewType.fragment: 'scope.md',
    ViewType.page: 'overview.html',
}
REQUIRED_TEMPLATES = tuple(set(fn for view in (VIEW_REPORT, VIEW_DETAIL, VIEW_TABLE, VIEW_SCOPE) for fn in view.values()))


# do I hate these globals, but I don't see another way with these frameworks
app = FastAPI()
security = HTTPBasic(realm="Compliance monitor", auto_error=True)  # use False for optional login
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
_scopes = {}  # map scope uuid to scope spec dict from YAML file


class TimestampEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return str(obj)
        # Let the base class default method raise the TypeError
        return super().default(obj)


def mk_conn(settings=settings):
    return psycopg2.connect(host=settings.db_host, user=settings.db_user,
                            password=settings.db_password, port=settings.db_port)


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
            acc_record = {'subject': account['subject'], 'roles': roles, 'group': account.get('group')}
            accountid = db_update_account(cur, acc_record)
            db_clear_delegates(cur, accountid)
            for delegate in account.get('delegates', ()):
                db_add_delegate(cur, accountid, delegate)
            keyids = set(db_update_apikey(cur, accountid, h) for h in account.get("api_keys", ()))
            db_filter_apikeys(cur, accountid, lambda keyid, *_: keyid in keyids)
            keyids = set(db_update_publickey(cur, accountid, key) for key in account.get("keys", ()))
            db_filter_publickeys(cur, accountid, lambda keyid, *_: keyid in keyids)
        conn.commit()


def _evaluate_version(version, scope_results):
    """evaluate the results for `version` and return the canonical JSON output"""
    target_results = {
        tname: {
            'testcases': tc_ids,
            'result': evaluate(scope_results, tc_ids),
        }
        for tname, tc_ids in version['targets'].items()
    }
    return {
        'result': target_results['main']['result'],
        'targets': target_results,
        'tc_target': version['tc_target'],
        'validity': version['validity'],
    }


def _evaluate_scope(spec, scope_results, include_drafts=False):
    """evaluate the results for `scope` and return the canonical JSON output"""
    testcases = spec['testcases']
    versions = spec['versions']
    version_results = {
        vname: _evaluate_version(version, scope_results)
        for vname, version in versions.items()
    }
    by_validity = defaultdict(list)
    for vname, version in versions.items():
        by_validity[version['validity']].append(vname)
    # go through worsening validity values until a passing version is found
    relevant = []
    best_passed = None
    for validity in ('effective', 'warn', 'deprecated'):
        vnames = by_validity[validity]
        relevant.extend(vnames)
        if any(version_results[vname]['result'] == 1 for vname in vnames):
            best_passed = validity
            break
    if include_drafts:
        relevant.extend(by_validity['draft'])
    passed = [vname for vname in relevant if version_results[vname]['result'] == 1]
    return {
        'name': spec['name'],
        'testcases': testcases,
        'results': scope_results,
        'buckets': {
            # sort testcase that occur any main target on top of those that don't
            res: sorted(tc_ids, key=lambda tc_id: (not testcases[tc_id]['attn'], tc_id))
            for res, tc_ids in eval_buckets(scope_results, testcases).items()
        },
        'versions': version_results,
        'relevant': relevant,
        'passed': passed,
        'passed_str': ', '.join([
            vname + ASTERISK_LOOKUP[versions[vname]['validity']]
            for vname in passed
        ]),
        'best_passed': best_passed,
    }


def _update_lookup(spec, target_dict):
    """Create entries in a lookup mapping for each testcase that occurs in this scope.

    This mapping from pairs (scope uuid, testcase id) to testcase facilitates
    evaluating result sets from database queries a great deal, because then just one lookup operation
    tells us whether a result row can be associated with any known testcase, and if so, whether the
    result is still valid (looking at the testcase's lifetime).

    In the future, the mapping could even be simplified by deriving a unique id from each pair that
    could then be stored (redundantly) in a dedicated database column, and the mapping could be from
    just one id (instead of a pair) to testcase.
    """
    scope_uuid = spec['uuid']
    for tc_id, testcase in spec['testcases'].items():
        target_dict[(scope_uuid, tc_id)] = testcase


def import_cert_yaml(yaml_path, target_dict):
    yaml = ruamel.yaml.YAML(typ='safe')
    with open(yaml_path, "r") as fileobj:
        spec = load_spec(yaml.load(fileobj.read()))
    annotate_validity(spec['timeline'], spec['versions'], date.today())
    target_dict[spec['uuid']] = spec
    _update_lookup(spec, target_dict)


def import_cert_yaml_dir(yaml_path, target_dict):
    for fn in sorted(os.listdir(yaml_path)):
        if fn.startswith('scs-') and fn.endswith('.yaml'):
            import_cert_yaml(os.path.join(yaml_path, fn), target_dict)


def get_scopes():
    """returns the scopes dict"""
    return _scopes


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
            if 'versions' not in document:
                # If this key is missing, this means we have a newer-style report that doesn't redundantly list
                # results per version. One reason for this change is that the meaning of a testcase identifier
                # no longer depends on the scope version, and we can quite simply read off the results from the
                # invocations. -- Use the dummy version '*' as long as the db schema still expects a version.
                document['versions'] = {'*': {
                    tc_id: {'result': result, 'invocation': inv_id}
                    for inv_id, invocation in document['run']['invocations'].items()
                    for tc_id, result in invocation['results'].items()
                }}
            for version, vdata in document['versions'].items():
                for check, rdata in vdata.items():
                    result = rdata['result']
                    approval = 1 == result  # pre-approve good result
                    db_insert_result2(cur, checked_at, subject, scopeuuid, version, check, result, approval, reportid)
    conn.commit()


def convert_result_rows_to_dict2(
    rows, scopes_lookup, grace_period_days=0, scopes=(), subjects=(), include_report=False, include_drafts=False,
):
    """evaluate all versions occurring in query result `rows`, returning canonical JSON representation"""
    now = datetime.now()
    if grace_period_days:
        now -= timedelta(days=grace_period_days)
    # collect result per subject/scope/version
    preliminary = defaultdict(lambda: defaultdict(dict))  # subject -> scope
    missing = set()
    for subject, scope_uuid, _, testcase_id, result, checked_at, report_uuid in rows:
        testcase = scopes_lookup.get((scope_uuid, testcase_id))
        if not testcase:
            # it can be False (testcase is known but version too old) or None (testcase not known)
            # only report the latter case
            if testcase is None:
                missing.add((scope_uuid, testcase_id))
            continue
        # drop value if too old
        lifetime = testcase.get('lifetime')  # leave None if not present; to be handled by add_period
        if now >= add_period(checked_at, lifetime):
            continue
        # don't use outdated value (FIXME only necessary as long as version column still in db!)
        tc_result = preliminary[subject][scope_uuid].get(testcase_id, {})
        if tc_result.get('checked_at', checked_at) > checked_at:
            continue
        tc_result.update(result=result, checked_at=checked_at)
        if include_report:
            tc_result.update(report=report_uuid)
        preliminary[subject][scope_uuid][testcase_id] = tc_result
    if missing:
        logger.warning('missing objects: ' + ', '.join(repr(x) for x in missing))
    # make sure the requested subjects and scopes are present (facilitates writing jinja2 templates)
    for subject in subjects:
        for scope in scopes:
            _ = preliminary[subject][scope]
    return {
        subject: {
            scope_uuid: _evaluate_scope(scopes_lookup[scope_uuid], scope_result, include_drafts=include_drafts)
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


def _build_report_url(base_url, report, *args, **kwargs):
    if kwargs.get('download'):
        return f"{base_url}reports/{report}"
    report_page = 'report_full' if kwargs.get('full') else 'report'
    url = f"{base_url}page/{report_page}/{report}"
    if len(args) == 2:  # version, testcase_id --> add corresponding fragment specifier
        url += f"#{args[1]}"  # version no longer relevant
    return url


def render_view(view, view_type, detail_page='detail', base_url='/', title=None, **kwargs):
    media_type = {ViewType.markdown: 'text/markdown'}.get(view_type, 'text/html')
    stage1 = stage2 = view[view_type]
    if view_type is ViewType.page:
        stage1 = view[ViewType.fragment]
    def scope_url(uuid): return f"{base_url}page/scope/{uuid}"  # noqa: E306,E704
    def detail_url(subject, scope): return f"{base_url}page/{detail_page}/{subject}/{scope}"  # noqa: E306,E704
    def report_url(report, *args, **kwargs): return _build_report_url(base_url, report, *args, **kwargs)  # noqa: E306,E704
    fragment = templates_map[stage1].render(base_url=base_url, detail_url=detail_url, report_url=report_url, scope_url=scope_url, **kwargs)
    if view_type != ViewType.markdown and stage1.endswith('.md'):
        fragment = markdown(fragment, extensions=['extra'])
    if stage1 != stage2:
        fragment = templates_map[stage2].render(fragment=fragment, title=title)
    return Response(content=fragment, media_type=media_type)


def _redact_report(report):
    """remove all lines from script output in `report` that are not directly linked to any testcase"""
    if 'run' not in report or 'invocations' not in report['run']:
        return
    for invdata in report['run']['invocations'].values():
        stdout = invdata.get('stdout', [])
        redacted = [line for line in stdout if line.rsplit(': ', 1)[-1] in ('PASS', 'ABORT', 'FAIL')]
        if len(redacted) != len(stdout):
            redacted.insert(0, '(the following has been redacted)')
            invdata['stdout'] = redacted
            invdata['redacted'] = True
        stderr = invdata.get('stderr', [])
        redacted = [line for line in stderr if line[:6] in ('WARNIN', 'ERROR:')]
        if len(redacted) != len(stderr):
            redacted.insert(0, '(the following has been redacted)')
            invdata['stderr'] = redacted
            invdata['redacted'] = True


@app.get("/{view_type}/report/{report_uuid}")
async def get_report_view(
    request: Request,
    conn: Annotated[connection, Depends(get_conn)],
    view_type: ViewType,
    report_uuid: str,
):
    with conn.cursor() as cur:
        specs = db_get_report(cur, report_uuid)
    if not specs:
        raise HTTPException(status_code=404)
    spec = specs[0]
    _redact_report(spec)
    return render_view(
        VIEW_REPORT, view_type, report=spec, base_url=settings.base_url,
        title=f'Report {report_uuid} (redacted)',
    )


@app.get("/{view_type}/report_full/{report_uuid}")
async def get_report_view_full(
    request: Request,
    account: Annotated[Optional[tuple[str, str]], Depends(auth)],
    conn: Annotated[connection, Depends(get_conn)],
    view_type: ViewType,
    report_uuid: str,
):
    with conn.cursor() as cur:
        specs = db_get_report(cur, report_uuid)
    if not specs:
        raise HTTPException(status_code=404)
    spec = specs[0]
    check_role(account, spec['subject'], ROLES['read_any'])
    return render_view(
        VIEW_REPORT, view_type, report=spec, base_url=settings.base_url,
        title=f'Report {report_uuid} (full)',
    )


def _resolve_group(cur, subject, prefix=GROUP_PREFIX):
    group = subject.removeprefix(prefix)
    if subject != group:
        return group, db_get_group(cur, group)
    return None, [subject]


@app.get("/{view_type}/detail/{subject}/{scopeuuid}")
async def get_detail(
    request: Request,
    conn: Annotated[connection, Depends(get_conn)],
    view_type: ViewType,
    subject: str,
    scopeuuid: str,
):
    with conn.cursor() as cur:
        group, subjects = _resolve_group(cur, subject)
        rows2 = []
        for subj in subjects:
            rows2.extend(db_get_relevant_results2(cur, subj, scopeuuid, approved_only=True))
    results2 = convert_result_rows_to_dict2(
        rows2, get_scopes(), include_report=True, grace_period_days=GRACE_PERIOD_DAYS,
        subjects=subjects, scopes=(scopeuuid, ),
    )
    title = f'Details for group {group}' if group else f'Details for subject {subject}'
    return render_view(
        VIEW_DETAIL, view_type, results=results2, base_url=settings.base_url,
        title=title,
    )


@app.get("/{view_type}/detail_full/{subject}/{scopeuuid}")
async def get_detail_full(
    request: Request,
    conn: Annotated[connection, Depends(get_conn)],
    view_type: ViewType,
    subject: str,
    scopeuuid: str,
):
    with conn.cursor() as cur:
        group, subjects = _resolve_group(cur, subject)
        rows2 = []
        for subj in subjects:
            rows2.extend(db_get_relevant_results2(cur, subj, scopeuuid, approved_only=False))
    results2 = convert_result_rows_to_dict2(
        rows2, get_scopes(), include_report=True, include_drafts=True,
        subjects=subjects, scopes=(scopeuuid, ),
    )
    title = f'Details for group {group}' if group else f'Details for subject {subject}'
    return render_view(
        VIEW_DETAIL, view_type, results=results2, base_url=settings.base_url,
        title=f'{title} (incl. unverified results)',
    )


@app.get("/{view_type}/table")
async def get_table(
    request: Request,
    conn: Annotated[connection, Depends(get_conn)],
    view_type: ViewType,
):
    with conn.cursor() as cur:
        rows2 = db_get_relevant_results2(cur, approved_only=True)
    results2 = convert_result_rows_to_dict2(rows2, get_scopes(), grace_period_days=GRACE_PERIOD_DAYS)
    return render_view(
        VIEW_TABLE, view_type, results=results2, base_url=settings.base_url, detail_page='detail',
        title="SCS compliance overview",
    )


@app.get("/{view_type}/table_full")
async def get_table_full(
    request: Request,
    conn: Annotated[connection, Depends(get_conn)],
    view_type: ViewType,
):
    with conn.cursor() as cur:
        rows2 = db_get_relevant_results2(cur, approved_only=False)
    results2 = convert_result_rows_to_dict2(rows2, get_scopes(), include_drafts=True)
    return render_view(
        VIEW_TABLE, view_type, results=results2, base_url=settings.base_url, detail_page='detail_full',
        title="SCS compliance overview (incl. unverified results)", unverified=True,
    )


@app.get("/{view_type}/scope/{scopeuuid}")
async def get_scope(
    request: Request,
    conn: Annotated[connection, Depends(get_conn)],
    view_type: ViewType,
    scopeuuid: str,
):
    spec = get_scopes()[scopeuuid]
    versions = spec['versions']
    # sort by name, and all drafts after all non-drafts
    column_data = [
        (version['_explicit_validity'].lower() == 'draft', name)
        for name, version in versions.items()
        if version['_explicit_validity']
    ]
    relevant = [name for _, name in sorted(column_data)]
    modules_chart = {}
    for name in relevant:
        for include in versions[name]['include']:
            module_id = include['module']['id']
            row = modules_chart.get(module_id)
            if row is None:
                row = modules_chart[module_id] = {'module': include['module'], 'columns': {}}
            row['columns'][name] = include
    rows = sorted(list(modules_chart.values()), key=lambda row: row['module']['id'])
    return render_view(VIEW_SCOPE, view_type, spec=spec, relevant=relevant, rows=rows, base_url=settings.base_url, title=spec['name'])


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


@app.get("/healthz")
async def get_healthz(request: Request):
    """return compliance monitor's health status"""
    credentials = await optional_security(request)
    authorized = credentials and \
        credentials.username == settings.hc_user and credentials.password == settings.hc_password

    try:
        mk_conn(settings=settings)
    except Exception as e:
        detail = str(e) if authorized else 'internal server error'
        return Response(status_code=500, content=detail, media_type='text/plain')

    return Response()  # empty response with status 200


def pick_filter(results, scope, *subjects):
    """Jinja filter to pick scope results from `results` for given `subject` and `scope`"""
    # simple case (backwards compatible): precisely one subject
    if len(subjects) == 1:
        return results.get(subjects[0], {}).get(scope, {})
    # generalized case: multiple subjects
    # in this case, drop None
    rs = [results.get(subject, {}).get(scope, {}) for subject in subjects]
    return [r for r in rs if r is not None]


STATUS_ORDERING = {
    'effective': 10,
    'warn': 5,
    'deprecated': 1,
}


def summary_filter(scope_results):
    """Jinja filter to construct summary from `scope_results`"""
    if not isinstance(scope_results, dict):
        # new generalized case: "aggregate" results for multiple subjects
        # simplified computation: just select the worst subject to represent the group
        scope_results = min(
            scope_results,
            default={},
            key=lambda sr: STATUS_ORDERING.get(sr.get('best_passed'), -1),
        )
    passed_str = scope_results.get('passed_str', '') or '–'
    best_passed = scope_results.get('best_passed')
    # avoid simple 🟢🔴 (hard to distinguish for color-blind folks)
    color = {
        'effective': '✅',
        'warn': '✅',  # forgo differentiation here in favor of simplicity (will be apparent in version list)
        'deprecated': '🟧',
    }.get(best_passed, '🛑')
    return f'{color} {passed_str}'


def verdict_filter(value):
    """Jinja filter to turn a canonical result value into a written verdict (PASS, MISS, or FAIL)"""
    # be fault-tolerant here and turn every non-canonical value into a MISS
    return {1: 'PASS', -1: 'FAIL'}.get(value, 'MISS')


def verdict_check_filter(value):
    """Jinja filter to turn a canonical result value into a symbolic verdict (✔, ⚠, or ✘)"""
    # be fault-tolerant here and turn every non-canonical value into a MISS
    return {1: '✔', -1: '✘'}.get(value, '⚠')


def reload_static_config(*args, do_ensure_schema=False):
    # allow arbitrary arguments so it can readily be used as signal handler
    logger.info("loading static config")
    scopes = {}
    import_cert_yaml_dir(settings.yaml_path, scopes)
    # import successful: only NOW destructively update global _scopes
    _scopes.clear()
    _scopes.update(scopes)
    import_templates(settings.template_path, env=env, templates=templates_map)
    validate_templates(templates=templates_map)
    with mk_conn(settings=settings) as conn:
        if do_ensure_schema:
            db_ensure_schema(conn)
        import_bootstrap(settings.bootstrap_path, conn=conn)


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    env.filters.update(
        pick=pick_filter,
        summary=summary_filter,
        verdict=verdict_filter,
        verdict_check=verdict_check_filter,
        markdown=markdown,
        validity_symbol=ASTERISK_LOOKUP.get,
    )
    reload_static_config(do_ensure_schema=True)
    signal.signal(signal.SIGHUP, reload_static_config)
    uvicorn.run(app, host='0.0.0.0', port=8080, log_level="info", workers=1)
