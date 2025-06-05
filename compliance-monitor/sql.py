from psycopg2 import sql
from psycopg2.extensions import cursor, connection

# list schema versions in ascending order
SCHEMA_VERSION_KEY = 'version'
SCHEMA_VERSIONS = ['v1', 'v2', 'v3', 'v4']
# use ... (Ellipsis) here to indicate that no default value exists (will lead to error if no value is given)
ACCOUNT_DEFAULTS = {'subject': ..., 'api_key': ..., 'roles': ..., 'group': None}
PUBLIC_KEY_DEFAULTS = {'public_key': ..., 'public_key_type': ..., 'public_key_name': ...}


class SchemaVersionError(Exception):
    pass


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


def db_ensure_schema_common(cur: cursor):
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
    ''')


def db_ensure_schema_v2(cur: cursor):
    db_ensure_schema_common(cur)
    cur.execute('''
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
    ''')


def db_ensure_schema_v3(cur: cursor):
    # v3 mainly extends v2, so we need v2 first
    db_ensure_schema_v2(cur)
    # We do alter the table "report" by dropping two columns, so these columns may have been created in vain
    # if this database never really was on v2, but I hope dropping columns from an empty table is cheap
    # enough, because I want to avoid having too many code paths here. We can remove these columns from
    # create table once all databases are on v3.
    cur.execute('''
    ALTER TABLE report DROP COLUMN IF EXISTS raw;
    ALTER TABLE report DROP COLUMN IF EXISTS rawformat;
    DROP TABLE IF EXISTS invocation;  -- we forgot this for post-upgrade v2, can be dropped without harm
    CREATE TABLE IF NOT EXISTS delegation (
        delegateid integer NOT NULL REFERENCES account ON DELETE CASCADE ON UPDATE CASCADE,
        accountid integer NOT NULL REFERENCES account ON DELETE CASCADE ON UPDATE CASCADE,
        UNIQUE (delegateid, accountid)
    );
    ''')


def db_ensure_schema_v4(cur: cursor):
    # start from v3, do small alteration
    db_ensure_schema_v2(cur)
    cur.execute('''
    ALTER TABLE account ADD COLUMN IF NOT EXISTS "group" text;
    ''')


def db_upgrade_data_v1_v2(cur):
    # we are going to drop table result, but use delete anyway to have the transaction safety
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
    ;
    DELETE FROM result
    ;''')


def db_post_upgrade_v1_v2(cur: cursor):
    cur.execute('''
    DROP TABLE IF EXISTS result;
    DROP TABLE IF EXISTS "check";
    DROP TABLE IF EXISTS standardentry;
    DROP TABLE IF EXISTS version;
    DROP TABLE IF EXISTS scope;
    ''')


def db_get_schema_version(cur: cursor):
    cur.execute('''SELECT value FROM meta WHERE key = %s;''', (SCHEMA_VERSION_KEY, ))
    return cur.rowcount and cur.fetchone()[0] or None


def db_set_schema_version(cur: cursor, version: str):
    cur.execute('''
    INSERT INTO meta (key, value)
    VALUES (%s, %s)
    ON CONFLICT (key)
    DO UPDATE
    SET value = EXCLUDED.value
    ;''', (SCHEMA_VERSION_KEY, version))


def db_upgrade_schema(conn: connection, cur: cursor):
    # the ensure_* and post_upgrade_* functions must be idempotent
    # ditto for the data transfer (ideally insert/delete transaction)
    # -- then, in case we get interrupted when setting the new version, the upgrade can be repeated
    # -- addendum: DDL is transactional with Postgres, so this effort was a bit in vain, but I keep it
    # that way just in case we want to use another database at some point
    while True:
        current = db_get_schema_version(cur)
        if current == SCHEMA_VERSIONS[-1]:
            break
        if current is None:
            # this is an empty db, but it also used to be the case with v1
            # I (mbuechse) made sure manually that the value v1 is set on running installations
            db_ensure_schema_v4(cur)
            db_set_schema_version(cur, 'v4')
            conn.commit()
        elif current == 'v1':
            db_ensure_schema_v2(cur)
            db_upgrade_data_v1_v2(cur)
            db_set_schema_version(cur, 'v1-v2')
            conn.commit()
        elif current == 'v1-v2':
            db_post_upgrade_v1_v2(cur)
            db_set_schema_version(cur, 'v2')
            conn.commit()
        elif current == 'v2':
            db_ensure_schema_v3(cur)
            db_set_schema_version(cur, 'v3')
            conn.commit()
        elif current == 'v3':
            db_ensure_schema_v4(cur)
            db_set_schema_version(cur, 'v4')
            conn.commit()


def db_ensure_schema(conn: connection):
    with conn.cursor() as cur:
        cur.execute('''
        CREATE TABLE IF NOT EXISTS meta (
            key text PRIMARY KEY,
            value text NOT NULL
        );
        ''')
        conn.commit()  # apparently, DDL is transactional with Postgres, so be sure to relieve the journal
        db_upgrade_schema(conn, cur)
    # the following could at some point be more adequate than the call to db_upgrade_schema above
    # -- namely, if the service is run as multiple processes and the upgrade must be done in advance --:
    # current, expected = db_get_schema_version(cur), SCHEMA_VERSIONS[-1]
    # if current != expected:
    #     raise SchemaVersionError(f"Database schema outdated! Expected {expected!r}, got {current!r}")


def db_update_account(cur: cursor, record: dict):
    sanitized = sanitize_record(record, ACCOUNT_DEFAULTS)
    cur.execute('''
    INSERT INTO account (subject, roles, "group")
    VALUES (%(subject)s, %(roles)s, %(group)s)
    ON CONFLICT (subject)
    DO UPDATE
    SET roles = EXCLUDED.roles,
    "group" = EXCLUDED."group"
    RETURNING accountid;''', sanitized)
    accountid, = cur.fetchone()
    return accountid


def db_clear_delegates(cur: cursor, accountid):
    cur.execute('''DELETE FROM delegation WHERE accountid = %s;''', (accountid, ))


def db_add_delegate(cur: cursor, accountid, delegate):
    cur.execute('''
    INSERT INTO delegation (accountid, delegateid)
    (SELECT %s, accountid
    FROM account
    WHERE subject = %s)
    RETURNING accountid;''', (accountid, delegate))


def db_find_subjects(cur: cursor, delegate):
    cur.execute('''
    SELECT a.subject
    FROM delegation
    JOIN account a ON a.accountid = delegation.accountid
    JOIN account b ON b.accountid = delegation.delegateid
    WHERE b.subject = %s;''', (delegate, ))
    return [row[0] for row in cur.fetchall()]


def db_get_group(cur: cursor, group):
    cur.execute('''SELECT subject FROM account WHERE "group" = %s;''', (group, ))
    return [row[0] for row in cur.fetchall()]


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


def db_get_report(cur: cursor, report_uuid):
    cur.execute(
        "SELECT data FROM report WHERE reportuuid = %(reportuuid)s;",
        {"reportuuid": report_uuid},
    )
    return [row[0] for row in cur.fetchall()]


def db_get_reports(cur: cursor, subject, limit, skip):
    cur.execute(
        sql.SQL("SELECT data FROM report {} LIMIT %(limit)s OFFSET %(skip)s;")
        .format(make_where_clause(
            None if not subject else sql.SQL('subject = %(subject)s'),
        )),
        {"subject": subject, "limit": limit, "skip": skip},
    )
    return [row[0] for row in cur.fetchall()]


def db_insert_report(cur: cursor, uuid, checked_at, subject, json_text):
    # this is an exception in that we don't use a record parameter (it's just not as practical here)
    cur.execute('''
    INSERT INTO report (reportuuid, checked_at, subject, data)
    VALUES (%s, %s, %s, %s)
    RETURNING reportid;''', (uuid, checked_at, subject, json_text))
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


def db_get_relevant_results2(
    cur: cursor,
    subject=None, scopeuuid=None, version=None, approved_only=True,
):
    """for each combination of scope/version/check, get the most recent test result that is still valid"""
    # find the latest result per subject/scopeuuid/version/checkid for this subject
    # DISTINCT ON is a Postgres-specific construct that comes in very handy here :)
    cur.execute(sql.SQL('''
    SELECT DISTINCT ON (subject, scopeuuid, version, testcase)
    result2.subject, scopeuuid, version, testcase, result, result2.checked_at, report.reportuuid
    FROM result2
    JOIN report ON report.reportid = result2.reportid
    {filter_condition}
    ORDER BY subject, scopeuuid, version, testcase, checked_at DESC;
    ''').format(
        filter_condition=make_where_clause(
            sql.SQL('approval') if approved_only else None,
            None if scopeuuid is None else sql.SQL('scopeuuid = %(scopeuuid)s'),
            None if version is None else sql.SQL('version = %(version)s'),
            None if subject is None else sql.SQL('result2.subject = %(subject)s'),
        ),
    ), {"subject": subject, "scopeuuid": scopeuuid, "version": version})
    return cur.fetchall()


def db_get_recent_results2(cur: cursor, approved, limit, skip, max_age_days=None):
    """list recent test results without grouping by scope/version/check"""
    columns = ('reportuuid', 'subject', 'checked_at', 'scopeuuid', 'version', 'check', 'result', 'approval')
    cur.execute(sql.SQL('''
    SELECT report.reportuuid, result2.subject, result2.checked_at, result2.scopeuuid, result2.version
    , result2.testcase, result2.result, result2.approval
    FROM result2
    NATURAL JOIN report
    {where_clause}
    ORDER BY checked_at
    LIMIT %(limit)s OFFSET %(skip)s;''').format(
        where_clause=make_where_clause(
            None if max_age_days is None else sql.SQL(
                f"checked_at > NOW() - interval '{max_age_days:d} days'"
            ),
            None if approved is None else sql.SQL('approval = %(approved)s'),
        ),
    ), {"limit": limit, "skip": skip, "approved": approved})
    return [{col: val for col, val in zip(columns, row)} for row in cur.fetchall()]


def db_patch_approval2(cur: cursor, record):
    cur.execute('''
    UPDATE result2
    SET approval = %(approval)s
    FROM report
    WHERE report.reportuuid = %(reportuuid)s
      AND result2.reportid = report.reportid
      AND result2.scopeuuid = %(scopeuuid)s
      AND result2.version = %(version)s
      AND result2.testcase = %(check)s
    RETURNING resultid;''', record)
    resultid, = cur.fetchone()
    return resultid
