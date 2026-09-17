"""
common/models/chart_of_code.py

Universal key-value store used by every module (HRMS, Inventory, Financial, etc.)

Table: ChartOfCode
──────────────────
Category    → module namespace       e.g. 'attendance_rules', 'inventory_settings'
Code        → feature within module  e.g. 'attendance_rules', 'item_defaults'
TypeCode    → individual setting key e.g. '3:late_grace_mins'  (dept_id:rule_key)
Description → value as string        e.g. '10'
EDate       → date last saved
ENo         → optional numeric ref   e.g. dept_id, item_id, employee_id

Usage
─────
from common.models.chart_of_code import ChartOfCode

# Save
ChartOfCode.set(db_alias, category='attendance_rules', code='attendance_rules',
                type_code='3:late_grace_mins', description='10', eno=3)

# Load all for a dept
rules = ChartOfCode.load(db_alias, category='attendance_rules', code='attendance_rules', eno=3)
# → {'late_grace_mins': '10', ...}  (strips '<eno>:' prefix automatically)

# Delete all for a dept
ChartOfCode.delete_all(db_alias, category='attendance_rules', code='attendance_rules', eno=3)

# Raw get
row = ChartOfCode.get(db_alias, type_code='3:late_grace_mins')
"""

import logging
from datetime import date
from typing import Optional

from django.db import connections

logger = logging.getLogger(__name__)

# ── SQL ───────────────────────────────────────────────────────────────────────

_DDL = """
CREATE TABLE IF NOT EXISTS "ChartOfCode" (
    "Category"    VARCHAR(50),
    "Code"        VARCHAR(50),
    "TypeCode"    VARCHAR(100),
    "Description" VARCHAR(500),
    "EDate"       DATE,
    "ENo"         INTEGER
)
"""

_IDX_CATEGORY = """
CREATE INDEX IF NOT EXISTS idx_chartofcode_cat_code
ON "ChartOfCode" ("Category", "Code")
"""

_IDX_ENO = """
CREATE INDEX IF NOT EXISTS idx_chartofcode_eno
ON "ChartOfCode" ("ENo")
"""

# ── Auto-migration: widen Category and Code if they are still on old narrow widths ──
_ALTER_WIDEN_COLS = """
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM   information_schema.columns
        WHERE  table_name              = 'ChartOfCode'
          AND  column_name             = 'Category'
          AND  character_maximum_length < 50
    ) THEN
        ALTER TABLE "ChartOfCode"
            ALTER COLUMN "Category" TYPE VARCHAR(50),
            ALTER COLUMN "Code"     TYPE VARCHAR(50);
    END IF;
END$$;
"""


# ── Ensure table ──────────────────────────────────────────────────────────────

def ensure_chart_of_code_table(db_alias: str) -> bool:
    """
    Create ChartOfCode + indexes if they don't exist.
    Also widens Category / Code columns from old VARCHAR(20/15) to VARCHAR(50)
    if the table was created with the previous narrow schema.
    Returns True on success, False on error.
    Safe to call on every request — all statements are idempotent.
    """
    try:
        conn = connections[db_alias]
        with conn.cursor() as cur:
            cur.execute(_DDL)
            cur.execute(_IDX_CATEGORY)
            cur.execute(_IDX_ENO)
            cur.execute(_ALTER_WIDEN_COLS)   # ← widens columns if needed
        return True
    except Exception as e:
        logger.warning('[ChartOfCode.ensure] %s on %s: %s', db_alias, db_alias, e)
        return False


# ── ORM-style class ───────────────────────────────────────────────────────────

class ChartOfCode:
    """
    Thin helper class — no Django ORM, works directly with raw SQL
    so it can operate on any customer DB alias.
    """

    TABLE = '"ChartOfCode"'

    # ── Low-level ─────────────────────────────────────────────────────────────

    @staticmethod
    def _conn(db_alias: str):
        return connections[db_alias]

    @classmethod
    def ensure(cls, db_alias: str):
        ensure_chart_of_code_table(db_alias)

    # ── Write ──────────────────────────────────────────────────────────────────

    @classmethod
    def set(cls, db_alias: str, *,
            category: str, code: str, type_code: str,
            description: str, eno: int = None, edate=None):
        """
        Upsert a single row.
        Uses DELETE + INSERT to stay compatible with all DB backends
        (avoids ON CONFLICT syntax differences between PostgreSQL / SQLite).
        """
        cls.ensure(db_alias)
        edate = edate or date.today().strftime('%Y-%m-%d')
        conn  = cls._conn(db_alias)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f'DELETE FROM {cls.TABLE} '
                    f'WHERE "Category"=%s AND "Code"=%s AND "TypeCode"=%s',
                    [category, code, type_code],
                )
                cur.execute(
                    f'INSERT INTO {cls.TABLE} '
                    f'("Category","Code","TypeCode","Description","EDate","ENo") '
                    f'VALUES (%s,%s,%s,%s,%s,%s)',
                    [category, code, type_code, str(description), edate, eno],
                )
            return True
        except Exception as e:
            logger.error('[ChartOfCode.set] %s', e, exc_info=True)
            return False

    @classmethod
    def set_many(cls, db_alias: str, *,
                 category: str, code: str,
                 eno: int = None,
                 items: dict,
                 key_prefix: str = ''):
        """
        Save a dict of {rule_key: value} as individual rows.
        Deletes all existing rows for (category, code, eno) first,
        then inserts one row per item.

        key_prefix is prepended to TypeCode:
            key_prefix=''          → TypeCode = rule_key
            key_prefix='3:'        → TypeCode = '3:rule_key'
            key_prefix=f'{eno}:'   → TypeCode = '<eno>:rule_key'  (recommended)
        """
        cls.ensure(db_alias)
        edate = date.today().strftime('%Y-%m-%d')
        conn  = cls._conn(db_alias)
        try:
            with conn.cursor() as cur:
                # Delete existing scope
                if eno is not None:
                    cur.execute(
                        f'DELETE FROM {cls.TABLE} '
                        f'WHERE "Category"=%s AND "Code"=%s AND "ENo"=%s',
                        [category, code, int(eno)],
                    )
                else:
                    cur.execute(
                        f'DELETE FROM {cls.TABLE} '
                        f'WHERE "Category"=%s AND "Code"=%s',
                        [category, code],
                    )
                saved = 0
                for key, value in items.items():
                    type_code = f'{key_prefix}{key}'
                    cur.execute(
                        f'INSERT INTO {cls.TABLE} '
                        f'("Category","Code","TypeCode","Description","EDate","ENo") '
                        f'VALUES (%s,%s,%s,%s,%s,%s)',
                        [category, code, type_code, str(value), edate, eno],
                    )
                    saved += 1
            return saved
        except Exception as e:
            logger.error('[ChartOfCode.set_many] %s', e, exc_info=True)
            return 0

    # ── Read ───────────────────────────────────────────────────────────────────

    @classmethod
    def get(cls, db_alias: str, *,
        category: str, code: str, type_code: str) -> Optional[str]:
        """Return the Description of a single row, or None."""
        cls.ensure(db_alias)
        try:
            with cls._conn(db_alias).cursor() as cur:
                cur.execute(
                    f'SELECT "Description" FROM {cls.TABLE} '
                    f'WHERE "Category"=%s AND "Code"=%s AND "TypeCode"=%s',
                    [category, code, type_code],
                )
                row = cur.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error('[ChartOfCode.get] %s', e, exc_info=True)
            return None

    @classmethod
    def load(cls, db_alias: str, *,
             category: str, code: str,
             eno: int = None,
             strip_prefix: str = '') -> dict:
        """
        Load all matching rows as {type_code: description}.

        If strip_prefix is given (e.g. '3:'), it is stripped from the
        start of each TypeCode before adding to the result dict:
            TypeCode '3:late_grace_mins' → key 'late_grace_mins'

        strip_prefix=f'{eno}:' is the standard pattern for per-entity rules.
        """
        cls.ensure(db_alias)
        try:
            conn   = cls._conn(db_alias)
            params = [category, code]
            sql    = (
                f'SELECT "TypeCode","Description" FROM {cls.TABLE} '
                f'WHERE "Category"=%s AND "Code"=%s'
            )
            if eno is not None:
                sql    += ' AND "ENo"=%s'
                params += [int(eno)]

            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()

            result = {}
            for type_code, description in rows:
                key = type_code
                if strip_prefix and key and key.startswith(strip_prefix):
                    key = key[len(strip_prefix):]
                result[key] = description or ''
            return result

        except Exception as e:
            logger.error('[ChartOfCode.load] %s', e, exc_info=True)
            return {}

    @classmethod
    def load_by_prefix(cls, db_alias: str, *,
                       category: str, code: str,
                       type_code_prefix: str) -> dict:
        """
        Load rows where TypeCode starts with a given prefix.
        Returns {type_code: description} with the full TypeCode as key.
        """
        cls.ensure(db_alias)
        try:
            with cls._conn(db_alias).cursor() as cur:
                cur.execute(
                    f'SELECT "TypeCode","Description" FROM {cls.TABLE} '
                    f'WHERE "Category"=%s AND "Code"=%s AND "TypeCode" LIKE %s',
                    [category, code, type_code_prefix + '%'],
                )
                return {tc: desc or '' for tc, desc in cur.fetchall()}
        except Exception as e:
            logger.error('[ChartOfCode.load_by_prefix] %s', e, exc_info=True)
            return {}

    # ── Delete ─────────────────────────────────────────────────────────────────

    @classmethod
    def delete_all(cls, db_alias: str, *,
                   category: str, code: str, eno: int = None):
        """Delete all rows for a category+code scope (optionally filtered by eno)."""
        cls.ensure(db_alias)
        try:
            conn   = cls._conn(db_alias)
            params = [category, code]
            sql    = f'DELETE FROM {cls.TABLE} WHERE "Category"=%s AND "Code"=%s'
            if eno is not None:
                sql    += ' AND "ENo"=%s'
                params += [int(eno)]
            with conn.cursor() as cur:
                cur.execute(sql, params)
            return True
        except Exception as e:
            logger.error('[ChartOfCode.delete_all] %s', e, exc_info=True)
            return False

    @classmethod
    def delete_one(cls, db_alias: str, *,
                   category: str, code: str, type_code: str):
        """Delete a single row by TypeCode."""
        cls.ensure(db_alias)
        try:
            with cls._conn(db_alias).cursor() as cur:
                cur.execute(
                    f'DELETE FROM {cls.TABLE} '
                    f'WHERE "Category"=%s AND "Code"=%s AND "TypeCode"=%s',
                    [category, code, type_code],
                )
            return True
        except Exception as e:
            logger.error('[ChartOfCode.delete_one] %s', e, exc_info=True)
            return False

    # ── Utility ────────────────────────────────────────────────────────────────

    @classmethod
    def list_categories(cls, db_alias: str) -> list:
        """List all distinct (Category, Code) pairs in the table."""
        cls.ensure(db_alias)
        try:
            with cls._conn(db_alias).cursor() as cur:
                cur.execute(
                    f'SELECT DISTINCT "Category","Code" FROM {cls.TABLE} '
                    f'ORDER BY "Category","Code"'
                )
                return [{'category': r[0], 'code': r[1]} for r in cur.fetchall()]
        except Exception as e:
            logger.error('[ChartOfCode.list_categories] %s', e, exc_info=True)
            return []