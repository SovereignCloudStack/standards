from psycopg2 import sql
from psycopg2.extensions import cursor

# use ... (Ellipsis) here to indicate that no default value exists (will lead to error if no value is given)
ACCOUNT_DEFAULTS = {'subject': ..., 'api_key': ..., 'roles': ...}
PUBLIC_KEY_DEFAULTS = {'public_key': ..., 'public_key_type': ..., 'public_key_name': ...}
SUBJECT_DEFAULTS = {'subject': ..., 'name': ..., 'provider': None, 'active': False}


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
    SELECT roles
    FROM account
    WHERE subject = %s;''', (subject, ))
    if not cur.rowcount:
        raise KeyError(subject)
    roles, = cur.fetchone()
    return roles


def db_get_apikeys(cur: cursor, subject):
    cur.execute('''
    SELECT apikeyhash
    FROM apikey
    NATURAL JOIN account
    WHERE subject = %s;''', (subject, ))
    return [row[0] for row in cur.fetchall()]


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
        roles integer
    );
    CREATE TABLE IF NOT EXISTS apikey (
        apikeyid SERIAL PRIMARY KEY,
        apikeyhash text,
        accountid integer NOT NULL REFERENCES account ON DELETE CASCADE ON UPDATE CASCADE,
        UNIQUE (accountid, apikeyhash)
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
    -- make a way simpler version that doesn't put that much background knowledge into the schema
    -- therefore let's hope the schema will be more robust against change
    CREATE TABLE IF NOT EXISTS result2 (
        resultid SERIAL PRIMARY KEY,
        -- some Python code to show how simple it is to fill this from a yaml report
        -- (using member access syntax instead of array access syntax for the dict fields)
        -- for vname, vres in report.versions.items():
        --    for tcid, tcres in vres.items():
        checked_at timestamp NOT NULL,  -- = report.checked_at
        subject text NOT NULL,          -- = report.subject
        scopeuuid text NOT NULL,        -- = report.spec.uuid
        version text NOT NULL,          -- = vname
        testcase text NOT NULL,         -- = tcid
        result int,                     -- = tcres.result
        approval boolean,               -- = tcres.result == 1
        -- the following is FYI only, for the most data is literally copied to this table
        reportid integer NOT NULL REFERENCES report ON DELETE CASCADE ON UPDATE CASCADE
    );
    CREATE TABLE IF NOT EXISTS subject (
        subject text PRIMARY KEY,
        active boolean,
        name text,
        provider text
    );
    ''')


def db_update_account(cur: cursor, record: dict):
    sanitized = sanitize_record(record, ACCOUNT_DEFAULTS)
    cur.execute('''
    INSERT INTO account (subject, roles)
    VALUES (%(subject)s, %(roles)s)
    ON CONFLICT (subject)
    DO UPDATE
    SET roles = EXCLUDED.roles
    RETURNING accountid;''', sanitized)
    accountid, = cur.fetchone()
    return accountid


def db_update_apikey(cur: cursor, accountid, apikey_hash):
    sanitized = dict(accountid=accountid, apikey_hash=apikey_hash)
    cur.execute('''
    INSERT INTO apikey (apikeyhash, accountid)
    VALUES (%(apikey_hash)s, %(accountid)s)
    ON CONFLICT (accountid, apikeyhash)
    DO UPDATE
    SET apikeyhash = EXCLUDED.apikeyhash  -- changes nothing, but necessary for RETURNING
    RETURNING apikeyid;''', sanitized)
    apikeyid, = cur.fetchone()
    return apikeyid


def db_filter_apikeys(cur: cursor, accountid, predicate: callable):
    cur.execute('SELECT apikeyid FROM apikey WHERE accountid = %s;', (accountid, ))
    removeids = [row[0] for row in cur.fetchall() if not predicate(*row)]
    while removeids:
        cur.execute('DELETE FROM apikey WHERE apikeyid IN %s', (tuple(removeids[:10]), ))
        del removeids[:10]


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


def db_get_reports(cur: cursor, subject, limit, skip):
    cur.execute(
        sql.SQL("SELECT data FROM report {} LIMIT %(limit)s OFFSET %(skip)s;")
        .format(make_where_clause(
            None if not subject else sql.SQL('subject = %(subject)s'),
        )),
        {"subject": subject, "limit": limit, "skip": skip},
    )
    return [row[0] for row in cur.fetchall()]


def db_insert_report(cur: cursor, uuid, checked_at, subject, json_text, content_type, body):
    # this is an exception in that we don't use a record parameter (it's just not as practical here)
    cur.execute('''
    INSERT INTO report (reportuuid, checked_at, subject, data, rawformat, raw)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING reportid;''', (uuid, checked_at, subject, json_text, content_type, body))
    reportid, = cur.fetchone()
    return reportid


def db_insert_result2(
    cur: cursor, checked_at, subject, scopeuuid, version, testcase, result, approval, reportid
):
    # this is an exception in that we don't use a record parameter (it's just not as practical here)
    cur.execute('''
    INSERT INTO result2 (checked_at, subject, scopeuuid, version, testcase, result, approval, reportid)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING resultid;''', (checked_at, subject, scopeuuid, version, testcase, result, approval, reportid))
    resultid, = cur.fetchone()
    return resultid


def db_copy_results(cur):
    cur.execute('''TRUNCATE TABLE result2;''')
    cur.execute('''
    INSERT INTO result2 (checked_at, subject, scopeuuid, version, testcase, result, approval, reportid)
    SELECT
        report.checked_at, report.subject,
        scope.scopeuuid, version.version, "check".id,
        result.result, result.approval, result.reportid
    FROM result
    NATURAL JOIN report
    NATURAL JOIN "check"
    NATURAL JOIN version
    NATURAL JOIN scope
    ;''')


def db_get_relevant_results2(
    cur: cursor,
    subject=None, scopeuuid=None, version=None, approved_only=True,
):
    """for each combination of scope/version/check, get the most recent test result that is still valid"""
    # find the latest result per subject/scopeuuid/version/checkid for this subject
    # DISTINCT ON is a Postgres-specific construct that comes in very handy here :)
    cur.execute(sql.SQL('''
    SELECT DISTINCT ON (subject, scopeuuid, version, testcase)
    subject, scopeuuid, version, testcase, result, checked_at FROM result2
    {filter_condition}
    ORDER BY subject, scopeuuid, version, testcase, checked_at DESC;
    ''').format(
        filter_condition=make_where_clause(
            sql.SQL('approval') if approved_only else None,
            None if scopeuuid is None else sql.SQL('scopeuuid = %(scopeuuid)s'),
            None if version is None else sql.SQL('version = %(version)s'),
            None if subject is None else sql.SQL('subject = %(subject)s'),
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


def db_get_subjects(cur: cursor, active: bool, limit, skip):
    """list subjects"""
    columns = ('subject', 'active', 'name', 'provider')
    cur.execute(sql.SQL('''
    SELECT subject, active, name, provider
    FROM subject
    {where_clause}
    LIMIT %(limit)s OFFSET %(skip)s;''').format(
        where_clause=make_where_clause(
            None if active is None else sql.SQL('active = %(active)s'),
        ),
    ), {"limit": limit, "skip": skip, "active": active})
    return [{col: val for col, val in zip(columns, row)} for row in cur.fetchall()]


def db_patch_subject(cur: cursor, record: dict):
    sanitized = sanitize_record(record, SUBJECT_DEFAULTS)
    cur.execute('''
    INSERT INTO subject (subject, active, name, provider)
    VALUES (%(subject)s, %(active)s, %(name)s, %(provider)s)
    ON CONFLICT (subject)
    DO UPDATE
    SET active = EXCLUDED.active, name = EXCLUDED.name, provider = EXCLUDED.provider
    ;''', sanitized)
