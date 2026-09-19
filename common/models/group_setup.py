# common/models/groups.py
"""
ItemGroups table definition for customer_db (PostgreSQL).
Converted from the original SQL Server schema used in group_setup views.

ensure_item_groups_table(db_alias) is passed as table_creator to BaseCRUD
and is called automatically when the table is missing.
"""

import logging
from django.db import connections
from django.db.utils import ProgrammingError, OperationalError

logger = logging.getLogger(__name__)


# ─── DDL ─────────────────────────────────────────────────────────────────────

CREATE_ITEM_GROUPS_SQL = """
CREATE TABLE IF NOT EXISTS "ItemGroups" (
    "GroupID"     INTEGER       NOT NULL,
    "Category"    INTEGER       NOT NULL,
    "Description" VARCHAR(200)  NOT NULL,
    "UCode"       VARCHAR(50),
    "Under"       INTEGER       DEFAULT 1,
    "NREC"        VARCHAR(50),

    CONSTRAINT "PK_ItemGroups" PRIMARY KEY ("GroupID")
);
"""

CREATE_ITEM_GROUPS_INDEXES_SQL = [
    'CREATE INDEX IF NOT EXISTS "idx_itemgroups_category" ON "ItemGroups" ("Category");',
    'CREATE INDEX IF NOT EXISTS "idx_itemgroups_desc"     ON "ItemGroups" ("Description");',
    'CREATE INDEX IF NOT EXISTS "idx_itemgroups_cat_lower_desc" ON "ItemGroups" ("Category", LOWER("Description"));',
]


# ─── Table creator ────────────────────────────────────────────────────────────

_ENSURED_ITEM_GROUPS_TABLES = set()


def ensure_item_groups_table(db_alias: str = 'customer_db', force: bool = False) -> bool:
    """
    Create the ItemGroups table + indexes on *db_alias* if they don't exist.
    Cached in memory so it executes at most once per process.

    Returns True  → table was just created.
    Returns False → table already existed (no-op).
    """
    if not force and db_alias in _ENSURED_ITEM_GROUPS_TABLES:
        return False

    try:
        conn = connections[db_alias]

        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1
                FROM   information_schema.tables
                WHERE  table_schema = 'public'
                AND    table_name   = 'ItemGroups'
            """)
            already_exists = cur.fetchone() is not None

        if already_exists:
            _ENSURED_ITEM_GROUPS_TABLES.add(db_alias)
            return False

        with conn.cursor() as cur:
            cur.execute(CREATE_ITEM_GROUPS_SQL)
            for idx_sql in CREATE_ITEM_GROUPS_INDEXES_SQL:
                cur.execute(idx_sql)

        logger.info('[common] Created ItemGroups table on db="%s"', db_alias)
        _ENSURED_ITEM_GROUPS_TABLES.add(db_alias)
        return True

    except (ProgrammingError, OperationalError) as e:
        logger.error('[common] ensure_item_groups_table failed: %s', e, exc_info=True)
        return False
    

     