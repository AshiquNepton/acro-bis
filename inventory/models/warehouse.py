# inventory/models/warehouse.py
"""
Warehouse master table.
Warehouses are also stored as ItemGroups rows (Category=16),
but this table holds the extended warehouse profile.
"""

import logging
from django.db import connections, OperationalError, ProgrammingError
from django.db import models

logger = logging.getLogger(__name__)

_ENSURED_WH_TABLES = set()


def ensure_warehouse_table(db_alias: str, force: bool = False) -> bool:
    """
    Create the Warehouse table if it does not already exist.
    Cached in memory so it runs at most once per process.
    """
    if not force and db_alias in _ENSURED_WH_TABLES:
        return True

    ddl = """
        CREATE TABLE IF NOT EXISTS "Warehouse" (
            "WarehouseID"   INT           NOT NULL,
            "WHCode"        VARCHAR(20)   NULL,
            "WHName"        VARCHAR(100)  NOT NULL,
            "Address1"      VARCHAR(100)  NULL,
            "Address2"      VARCHAR(100)  NULL,
            "Address3"      VARCHAR(100)  NULL,
            "Phone"         VARCHAR(25)   NULL,
            "Mobile"        VARCHAR(25)   NULL,
            "Email"         VARCHAR(50)   NULL,
            "Under"         INT           NULL DEFAULT 0,
            "Status"        SMALLINT      NULL DEFAULT 1,
            "CreatedAt"     TIMESTAMP     NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "PK_Warehouse" PRIMARY KEY ("WarehouseID")
        );
        CREATE INDEX IF NOT EXISTS "idx_warehouse_whname"
            ON "Warehouse" ("WHName");
        CREATE INDEX IF NOT EXISTS "idx_warehouse_status"
            ON "Warehouse" ("Status");
    """

    _migrate_alters = [
        'ALTER TABLE "Warehouse" ADD COLUMN IF NOT EXISTS "WHCode"   VARCHAR(20)  NULL',
        'ALTER TABLE "Warehouse" ADD COLUMN IF NOT EXISTS "Address1" VARCHAR(100) NULL',
        'ALTER TABLE "Warehouse" ADD COLUMN IF NOT EXISTS "Address2" VARCHAR(100) NULL',
        'ALTER TABLE "Warehouse" ADD COLUMN IF NOT EXISTS "Address3" VARCHAR(100) NULL',
        'ALTER TABLE "Warehouse" ADD COLUMN IF NOT EXISTS "Phone"    VARCHAR(25)  NULL',
        'ALTER TABLE "Warehouse" ADD COLUMN IF NOT EXISTS "Mobile"   VARCHAR(25)  NULL',
        'ALTER TABLE "Warehouse" ADD COLUMN IF NOT EXISTS "Email"    VARCHAR(50)  NULL',
        'ALTER TABLE "Warehouse" ADD COLUMN IF NOT EXISTS "Under"    INT          NULL DEFAULT 0',
        'ALTER TABLE "Warehouse" ADD COLUMN IF NOT EXISTS "Status"   SMALLINT     NULL DEFAULT 1',
        'ALTER TABLE "Warehouse" ADD COLUMN IF NOT EXISTS "CreatedAt" TIMESTAMP   NULL DEFAULT CURRENT_TIMESTAMP',
    ]

    try:
        with connections[db_alias].cursor() as cur:
            cur.execute(ddl)
            for sql in _migrate_alters:
                try:
                    cur.execute(sql)
                except Exception:
                    pass
        _ENSURED_WH_TABLES.add(db_alias)
        logger.debug('ensure_warehouse_table: table ready in %s', db_alias)
        return True
    except (OperationalError, ProgrammingError) as exc:
        logger.error('ensure_warehouse_table: could not create/migrate table in %s: %s', db_alias, exc)
        return False


class Warehouse(models.Model):
    """ORM model for Warehouse table. managed=False."""
    WarehouseID = models.IntegerField(primary_key=True, db_column='WarehouseID')
    WHCode      = models.CharField(max_length=20,  null=True, blank=True, db_column='WHCode')
    WHName      = models.CharField(max_length=100, db_column='WHName')
    Address1    = models.CharField(max_length=100, null=True, blank=True, db_column='Address1')
    Address2    = models.CharField(max_length=100, null=True, blank=True, db_column='Address2')
    Address3    = models.CharField(max_length=100, null=True, blank=True, db_column='Address3')
    Phone       = models.CharField(max_length=25,  null=True, blank=True, db_column='Phone')
    Mobile      = models.CharField(max_length=25,  null=True, blank=True, db_column='Mobile')
    Email       = models.CharField(max_length=50,  null=True, blank=True, db_column='Email')
    Under       = models.IntegerField(null=True, blank=True, default=0, db_column='Under')
    Status      = models.SmallIntegerField(null=True, blank=True, default=1, db_column='Status')
    CreatedAt   = models.DateTimeField(null=True, blank=True, db_column='CreatedAt')

    class Meta:
        db_table = 'Warehouse'
        managed  = False
