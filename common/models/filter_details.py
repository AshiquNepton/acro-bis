# common/models/filter_details.py
"""
FilterDetails table definition for customer_db (PostgreSQL).

ensure_filter_details_table(db_alias):
  - Creates the table with PK constraint if it does not exist.
  - If the table already exists WITHOUT the PK constraint (created before
    this version), it adds the constraint in-place so ON CONFLICT upserts
    work correctly.
"""

import logging
from django.db import connections
from django.db.utils import ProgrammingError, OperationalError

logger = logging.getLogger(__name__)


CREATE_FILTER_DETAILS_SQL = """
CREATE TABLE IF NOT EXISTS "FilterDetails" (
    "ReportName"  VARCHAR(20),
    "FieldName"   VARCHAR(20),
    "DisplayName" VARCHAR(20),
    "FieldType"   SMALLINT,
    "FilterSql"   VARCHAR(150),
    "ColWidth"    VARCHAR(15),
    "IDField"     VARCHAR(20),
    "Default"     SMALLINT    DEFAULT 0,
    "Operator"    INTEGER     DEFAULT 0,

    CONSTRAINT "PK_FilterDetails" PRIMARY KEY ("ReportName", "FieldName")
);
"""

CREATE_FILTER_DETAILS_INDEXES_SQL = [
    'CREATE INDEX IF NOT EXISTS "idx_filterdetails_report"  ON "FilterDetails" ("ReportName");',
    'CREATE INDEX IF NOT EXISTS "idx_filterdetails_default" ON "FilterDetails" ("ReportName", "Default");',
]


_ENSURED_FILTER_TABLES = set()


def ensure_filter_details_table(db_alias: str = 'customer_db', force: bool = False) -> bool:
    """
    Create the FilterDetails table + indexes if they don't exist.
    Also repairs missing PK constraint on tables created by older code.
    Cached in memory so it executes at most once per process.

    Returns True  → table was just created.
    Returns False → table already existed (may have applied constraint fix).
    """
    if not force and db_alias in _ENSURED_FILTER_TABLES:
        return False

    try:
        conn = connections[db_alias]

        with conn.cursor() as cur:
            # ── Does the table exist? ─────────────────────────────────────
            cur.execute("""
                SELECT 1
                FROM   information_schema.tables
                WHERE  table_schema = 'public'
                AND    table_name   = 'FilterDetails'
            """)
            table_exists = cur.fetchone() is not None

        if not table_exists:
            # Fresh install — create with PK included
            with conn.cursor() as cur:
                cur.execute(CREATE_FILTER_DETAILS_SQL)
                for idx_sql in CREATE_FILTER_DETAILS_INDEXES_SQL:
                    cur.execute(idx_sql)
            logger.info('[common] Created FilterDetails table on db="%s"', db_alias)
            _ENSURED_FILTER_TABLES.add(db_alias)
            return True

        # ── Table exists — check whether PK constraint is present ─────────
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1
                FROM   information_schema.table_constraints
                WHERE  table_schema     = 'public'
                AND    table_name       = 'FilterDetails'
                AND    constraint_name  = 'PK_FilterDetails'
                AND    constraint_type  = 'PRIMARY KEY'
            """)
            pk_exists = cur.fetchone() is not None

        if not pk_exists:
            # Older table without the PK — add it now.
            # First remove any duplicate (ReportName, FieldName) pairs that
            # would block the constraint, keeping the last-inserted row.
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM "FilterDetails" fd1
                    USING  "FilterDetails" fd2
                    WHERE  fd1.ctid   < fd2.ctid
                    AND    fd1."ReportName" = fd2."ReportName"
                    AND    fd1."FieldName"  = fd2."FieldName"
                """)
                cur.execute("""
                    ALTER TABLE "FilterDetails"
                    ADD CONSTRAINT "PK_FilterDetails"
                    PRIMARY KEY ("ReportName", "FieldName")
                """)
            logger.info(
                '[common] Added PK_FilterDetails constraint on db="%s"', db_alias
            )

        _ENSURED_FILTER_TABLES.add(db_alias)
        return False

    except (ProgrammingError, OperationalError) as e:
        logger.error('[common] ensure_filter_details_table failed: %s', e, exc_info=True)
        return False