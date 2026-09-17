# common/utils/document_utils.py
"""
Universal Document Utility — table definition + shared helpers.
Works across ALL modules (hrms, laundry, restaurant, inventory, financial).

One table "Documents" with Module + RefID to identify the owner.

FTP folder:  /erp/{module}/{company_code}/{ref_id}/{group_id}/filename

Import in any view:
    from common.utils.document_utils import ensure_documents_table, get_group_label
"""

import logging
from django.db import connections
from django.db.utils import ProgrammingError, OperationalError

logger = logging.getLogger(__name__)


# ─── DDL ─────────────────────────────────────────────────────────────────────

CREATE_DOCUMENTS_SQL = """
CREATE TABLE IF NOT EXISTS "Documents" (
    "DocID"        SERIAL         PRIMARY KEY,
    "Module"       VARCHAR(50)    NOT NULL,
    "RefID"        VARCHAR(50)    NOT NULL,
    "Doc"          VARCHAR(300),
    "GroupID"      INTEGER,
    "DeliveredBy"  VARCHAR(200),
    "ReceivedBy"   VARCHAR(200),
    "ContactNo"    VARCHAR(50),
    "DocDate"      DATE,
    "Notes"        TEXT,
    "Details"      TEXT,
    "FilePath"     VARCHAR(500),
    "CreatedAt"    TIMESTAMP      DEFAULT NOW()
);
"""

CREATE_DOCUMENTS_INDEXES = [
    'CREATE INDEX IF NOT EXISTS "idx_docs_module_refid" ON "Documents" ("Module","RefID");',
    'CREATE INDEX IF NOT EXISTS "idx_docs_groupid"      ON "Documents" ("GroupID");',
]


def ensure_documents_table(db_alias: str = 'customer_db') -> bool:
    """
    Auto-create the Documents table if it doesn't exist.
    Returns True if created, False if already existed.
    Same pattern as all other ensure_* in the project.
    """
    try:
        conn = connections[db_alias]
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'Documents'
            """)
            if cur.fetchone():
                return False
        with conn.cursor() as cur:
            cur.execute(CREATE_DOCUMENTS_SQL)
            for idx in CREATE_DOCUMENTS_INDEXES:
                cur.execute(idx)
        logger.info('[Documents] Table created on "%s"', db_alias)
        return True
    except (ProgrammingError, OperationalError) as e:
        logger.error('[Documents] ensure_documents_table: %s', e)
        return False


def get_group_label(db_alias: str, group_id) -> str:
    """Fetch Description from ItemGroups for a given GroupID."""
    if not group_id:
        return ''
    try:
        with connections[db_alias].cursor() as cur:
            cur.execute(
                'SELECT "Description" FROM "ItemGroups" WHERE "GroupID" = %s',
                [group_id]
            )
            row = cur.fetchone()
            return row[0] if row else ''
    except Exception:
        return ''