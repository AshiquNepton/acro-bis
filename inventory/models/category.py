# inventory/models/category.py
"""
Category / ItemGroup extended profile table.

The ItemGroups table (in common/models/group_setup.py) holds all group entries
identified by Category (typecode) and GroupID.  This table is an optional
extended profile for groups that need more metadata (e.g. a Category image,
sort order, parent hierarchy beyond what ItemGroups.Under provides).
"""

import logging
from django.db import connections, OperationalError, ProgrammingError
from django.db import models

logger = logging.getLogger(__name__)

_ENSURED_CAT_TABLES = set()


def ensure_category_table(db_alias: str, force: bool = False) -> bool:
    """
    Create the Category extended-profile table if it does not already exist.
    Cached in memory so it runs at most once per process.
    """
    if not force and db_alias in _ENSURED_CAT_TABLES:
        return True

    ddl = """
        CREATE TABLE IF NOT EXISTS "Category" (
            "CategoryID"    INT           NOT NULL,
            "CatCode"       VARCHAR(20)   NULL,
            "CatName"       VARCHAR(100)  NOT NULL,
            "ParentID"      INT           NULL DEFAULT 0,
            "TypeCode"      INT           NULL,
            "SortOrder"     INT           NULL DEFAULT 0,
            "ImagePath"     VARCHAR(200)  NULL,
            "Status"        SMALLINT      NULL DEFAULT 1,
            "CreatedAt"     TIMESTAMP     NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "PK_Category" PRIMARY KEY ("CategoryID")
        );
        CREATE INDEX IF NOT EXISTS "idx_category_catname"
            ON "Category" ("CatName");
        CREATE INDEX IF NOT EXISTS "idx_category_typecode"
            ON "Category" ("TypeCode");
        CREATE INDEX IF NOT EXISTS "idx_category_parentid"
            ON "Category" ("ParentID");
    """

    _migrate_alters = [
        'ALTER TABLE "Category" ADD COLUMN IF NOT EXISTS "CatCode"   VARCHAR(20)  NULL',
        'ALTER TABLE "Category" ADD COLUMN IF NOT EXISTS "ParentID"  INT          NULL DEFAULT 0',
        'ALTER TABLE "Category" ADD COLUMN IF NOT EXISTS "TypeCode"  INT          NULL',
        'ALTER TABLE "Category" ADD COLUMN IF NOT EXISTS "SortOrder" INT          NULL DEFAULT 0',
        'ALTER TABLE "Category" ADD COLUMN IF NOT EXISTS "ImagePath" VARCHAR(200) NULL',
        'ALTER TABLE "Category" ADD COLUMN IF NOT EXISTS "Status"    SMALLINT     NULL DEFAULT 1',
        'ALTER TABLE "Category" ADD COLUMN IF NOT EXISTS "CreatedAt" TIMESTAMP    NULL DEFAULT CURRENT_TIMESTAMP',
    ]

    try:
        with connections[db_alias].cursor() as cur:
            cur.execute(ddl)
            for sql in _migrate_alters:
                try:
                    cur.execute(sql)
                except Exception:
                    pass
        _ENSURED_CAT_TABLES.add(db_alias)
        logger.debug('ensure_category_table: table ready in %s', db_alias)
        return True
    except (OperationalError, ProgrammingError) as exc:
        logger.error('ensure_category_table: could not create/migrate table in %s: %s', db_alias, exc)
        return False


class Category(models.Model):
    """ORM model for Category table. managed=False."""
    CategoryID = models.IntegerField(primary_key=True, db_column='CategoryID')
    CatCode    = models.CharField(max_length=20,  null=True, blank=True, db_column='CatCode')
    CatName    = models.CharField(max_length=100, db_column='CatName')
    ParentID   = models.IntegerField(null=True, blank=True, default=0, db_column='ParentID')
    TypeCode   = models.IntegerField(null=True, blank=True, db_column='TypeCode')
    SortOrder  = models.IntegerField(null=True, blank=True, default=0, db_column='SortOrder')
    ImagePath  = models.CharField(max_length=200, null=True, blank=True, db_column='ImagePath')
    Status     = models.SmallIntegerField(null=True, blank=True, default=1, db_column='Status')
    CreatedAt  = models.DateTimeField(null=True, blank=True, db_column='CreatedAt')

    class Meta:
        db_table = 'Category'
        managed  = False
