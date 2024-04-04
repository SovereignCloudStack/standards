from psycopg2 import sql
from psycopg2.extensions import cursor

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


def db_find_account(cur: cursor, subject):
    cur.execute('''
    SELECT apikey, roles
    FROM account
    WHERE subject = %s;''', (subject, ))
    return cur.fetchone()


def db_get_keys(cur: cursor, subject):
    cur.execute('''
    SELECT keytype, key
    FROM publickey
    NATURAL JOIN account
    WHERE subject = %s;''', (subject, ))
    return cur.fetchall()


def db_ensure_schema(cur: cursor):
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


def db_update_account(cur: cursor, record: dict):
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


def db_update_publickey(cur: cursor, accountid, record: dict):
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


def db_filter_publickeys(cur: cursor, accountid, predicate: callable):
    cur.execute('SELECT keyid, keyname FROM publickey WHERE accountid = %s;', (accountid, ))
    removeids = [row[0] for row in cur.fetchall() if not predicate(*row)]
    while removeids:
        cur.execute('DELETE FROM publickey WHERE keyid IN %s', (tuple(removeids[:10]), ))
        del removeids[:10]


def db_update_scope(cur: cursor, record: dict):
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


def db_update_version(cur: cursor, scopeid, record: dict):
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


def db_update_standard(cur: cursor, versionid, record: dict):
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


def db_update_check(cur: cursor, versionid, standardid, record: dict):
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


def db_filter_checks(cur: cursor, standardid, predicate: callable):
    cur.execute('SELECT checkid, id FROM "check" WHERE standardid = %s;', (standardid, ))
    removeids = [row[0] for row in cur.fetchall() if not predicate(*row)]
    while removeids:
        cur.execute('DELETE FROM "check" WHERE checkid IN %s', (tuple(removeids[:10]), ))
        del removeids[:10]


def db_filter_standards(cur: cursor, versionid, predicate: callable):
    cur.execute('SELECT standardid, surl FROM standardentry WHERE versionid = %s;', (versionid, ))
    removeids = [row[0] for row in cur.fetchall() if not predicate(*row)]
    while removeids:
        cur.execute('DELETE FROM standardentry WHERE standardid IN %s', (tuple(removeids[:10]), ))
        del removeids[:10]


def db_filter_versions(cur: cursor, scopeid, predicate: callable):
    cur.execute('SELECT versionid, version FROM version WHERE scopeid = %s;', (scopeid, ))
    removeids = [row[0] for row in cur.fetchall() if not predicate(*row)]
    while removeids:
        cur.execute('DELETE FROM version WHERE versionid IN %s', (tuple(removeids[:10]), ))
        del removeids[:10]


def db_get_reports(cur: cursor, subject, limit, skip):
    cur.execute(
        sql.SQL("SELECT data FROM report {} LIMIT %(limit)s OFFSET %(skip)s;")
        .format(make_where_clause(
            None if not subject else sql.SQL('subject = %(subject)s'),
        )),
        {"subject": subject, "limit": limit, "skip": skip},
    )
    return [row[0] for row in cur.fetchall()]


def db_get_scopeid(cur: cursor, scopeuuid):
    cur.execute('SELECT scopeid FROM scope WHERE scopeuuid = %s;', (scopeuuid, ))
    scopeid, = cur.fetchone()
    return scopeid


def db_insert_report(cur: cursor, uuid, checked_at, subject, json_text, content_type, body):
    # this is an exception in that we don't use a record parameter (it's just not as practical here)
    cur.execute('''
    INSERT INTO report (reportuuid, checked_at, subject, data, rawformat, raw)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING reportid;''', (uuid, checked_at, subject, json_text, content_type, body))
    reportid, = cur.fetchone()
    return reportid


def db_insert_invocation(cur: cursor, reportid, invocation, record):
    sanitized = sanitize_record(record, INVOCATION_DEFAULTS, reportid=reportid, invocation=invocation)
    cur.execute('''
    INSERT INTO invocation (reportid, invocation, critical, error, warning, result)
    VALUES (%(reportid)s, %(invocation)s, %(critical)s, %(error)s, %(warning)s, %(result)s)
    RETURNING invocationid;''', sanitized)
    invocationid, = cur.fetchone()
    return invocationid


def db_get_versionid(cur: cursor, scopeid, version):
    cur.execute('SELECT versionid FROM version WHERE scopeid = %s AND version = %s;', (scopeid, version))
    versionid, = cur.fetchone()
    return versionid


def db_get_checkdata(cur: cursor, versionid, check):
    cur.execute('SELECT checkid, lifetime FROM "check" WHERE versionid = %s AND id = %s;', (versionid, check))
    return cur.fetchone()


def db_insert_result(cur: cursor, reportid, invocationid, checkid, result, approval, expiration):
    # this is an exception in that we don't use a record parameter (it's just not as practical here)
    cur.execute('''
    INSERT INTO result (reportid, invocationid, checkid, result, approval, expiration)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING resultid;''', (reportid, invocationid, checkid, result, approval, expiration))
    resultid, = cur.fetchone()
    return resultid


def db_get_relevant_results(
    cur: cursor, subject, scopeuuid, version, approved_only=True, grace_period_days=None,
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


def db_get_recent_results(cur: cursor, approved, limit, skip, grace_period_days=None):
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
            sql.SQL(
                'expiration > NOW()' if grace_period_days is None else
                f"expiration > NOW() - interval '{grace_period_days:d} days'"
            ),
            None if approved is None else sql.SQL('approval = %(approved)s'),
        ),
    ), {"limit": limit, "skip": skip, "approved": approved})
    return [{col: val for col, val in zip(columns, row)} for row in cur.fetchall()]


def db_patch_approval(cur: cursor, record):
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
