import logging
import json
from django.db import connections, OperationalError, ProgrammingError
from django.db import models

logger = logging.getLogger(__name__)

_ENSURED_STOCK_TABLES = set()


def ensure_stocks_table(db_alias: str, force: bool = False) -> bool:
    """
    Create the Stocks table in the given database alias if it does not
    already exist. Cached in memory so it executes at most once per process.

    Schema (current):
      PK  : ItemID  (one price row per item for Item Master)
      Rate0–Rate5 : six configurable selling rates (Rate0 = Purchase Price)
      PurchasePrice column DROPPED — Rate0 is the single source of truth.

    Multi-unit pricing is stored in two complementary ways:
      1. MultiUnitData TEXT  — full JSON blob from the MultiUnitManager widget
      2. Unit{n}_{field} NUMERIC — flattened per-unit rates for fast SQL queries
    """
    if not force and db_alias in _ENSURED_STOCK_TABLES:
        return True

    ddl = """
        CREATE TABLE IF NOT EXISTS "Stocks" (
            -- Identity
            "StockID"          SERIAL          NOT NULL,
            "ItemID"           INT             NOT NULL,

            -- Selling Rates (Rate0 = Purchase Price — 6 configurable price levels)
            "Rate0"            NUMERIC(19,4)   NULL  DEFAULT 0,
            "Rate1"            NUMERIC(19,4)   NULL  DEFAULT 0,
            "Rate2"            NUMERIC(19,4)   NULL,
            "Rate3"            NUMERIC(19,4)   NULL,
            "Rate4"            NUMERIC(19,4)   NULL,
            "Rate5"            NUMERIC(19,4)   NULL,
            "LUCost"           NUMERIC(19,4)   NULL,

            -- Vendor / Firm
            "FirmID"           INT             NULL,
            "Vendor"           INT             NULL,

            -- Discount Rates
            "Discount"         NUMERIC(19,4)   NULL,
            "SpecialDiscount"  NUMERIC(19,4)   NULL,
            "PurchaseDiscount" NUMERIC(19,4)   NULL,

            -- Date / Reference
            "PurchaseDate"     TIMESTAMP       NULL,
            "BillNo"           VARCHAR(20)     NULL,
            "StockDate"        TIMESTAMP       NULL,

            -- Multi-Unit Pricing (JSON blob — full MultiUnitManager output)
            "MultiUnitData"    TEXT            NULL,

            -- Multi-Unit Pricing (flattened columns for fast queries, up to 6 units)
            "Unit1BaseRate"   NUMERIC(19,4)   NULL,
            "Unit1MRPRate"    NUMERIC(19,4)   NULL,
            "Unit1DRPRate"    NUMERIC(19,4)   NULL,
            "Unit1FDPRate"    NUMERIC(19,4)   NULL,
            "Unit1BranchRate" NUMERIC(19,4)   NULL,

            "Unit2BaseRate"   NUMERIC(19,4)   NULL,
            "Unit2MRPRate"    NUMERIC(19,4)   NULL,
            "Unit2DRPRate"    NUMERIC(19,4)   NULL,
            "Unit2FDPRate"    NUMERIC(19,4)   NULL,
            "Unit2BranchRate" NUMERIC(19,4)   NULL,

            "Unit3BaseRate"   NUMERIC(19,4)   NULL,
            "Unit3MRPRate"    NUMERIC(19,4)   NULL,
            "Unit3DRPRate"    NUMERIC(19,4)   NULL,
            "Unit3FDPRate"    NUMERIC(19,4)   NULL,
            "Unit3BranchRate" NUMERIC(19,4)   NULL,

            "Unit4BaseRate"   NUMERIC(19,4)   NULL,
            "Unit4MRPRate"    NUMERIC(19,4)   NULL,
            "Unit4DRPRate"    NUMERIC(19,4)   NULL,
            "Unit4FDPRate"    NUMERIC(19,4)   NULL,
            "Unit4BranchRate" NUMERIC(19,4)   NULL,

            "Unit5BaseRate"   NUMERIC(19,4)   NULL,
            "Unit5MRPRate"    NUMERIC(19,4)   NULL,
            "Unit5DRPRate"    NUMERIC(19,4)   NULL,
            "Unit5FDPRate"    NUMERIC(19,4)   NULL,
            "Unit5BranchRate" NUMERIC(19,4)   NULL,

            "Unit6BaseRate"   NUMERIC(19,4)   NULL,
            "Unit6MRPRate"    NUMERIC(19,4)   NULL,
            "Unit6DRPRate"    NUMERIC(19,4)   NULL,
            "Unit6FDPRate"    NUMERIC(19,4)   NULL,
            "Unit6BranchRate" NUMERIC(19,4)   NULL,

            -- Constraints
            CONSTRAINT "PK_STKID"  UNIQUE  ("StockID"),
            CONSTRAINT "PK_Stock"  PRIMARY KEY ("ItemID"),
            CONSTRAINT "FK_Stocks_Item" FOREIGN KEY ("ItemID")
                REFERENCES "InventoryItems" ("ItemID") ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS "idx_stocks_itemid" ON "Stocks" ("ItemID");
    """

    # Incremental ALTER — adds missing columns on existing DBs without touching the PK
    _migrate_sql = [
        # Add any missing rate columns
        'ALTER TABLE "Stocks" ADD COLUMN IF NOT EXISTS "Rate0"  NUMERIC(19,4) NULL DEFAULT 0',
        'ALTER TABLE "Stocks" ADD COLUMN IF NOT EXISTS "Rate1"  NUMERIC(19,4) NULL DEFAULT 0',
        'ALTER TABLE "Stocks" ADD COLUMN IF NOT EXISTS "Rate2"  NUMERIC(19,4) NULL',
        'ALTER TABLE "Stocks" ADD COLUMN IF NOT EXISTS "Rate3"  NUMERIC(19,4) NULL',
        'ALTER TABLE "Stocks" ADD COLUMN IF NOT EXISTS "Rate4"  NUMERIC(19,4) NULL',
        'ALTER TABLE "Stocks" ADD COLUMN IF NOT EXISTS "Rate5"  NUMERIC(19,4) NULL',
        'ALTER TABLE "Stocks" ADD COLUMN IF NOT EXISTS "LUCost" NUMERIC(19,4) NULL',
        # Multi-unit columns
        'ALTER TABLE "Stocks" ADD COLUMN IF NOT EXISTS "MultiUnitData" TEXT NULL',
        *[
            f'ALTER TABLE "Stocks" ADD COLUMN IF NOT EXISTS "Unit{i}{r}" NUMERIC(19,4) NULL'
            for i in range(1, 7)
            for r in ('BaseRate', 'MRPRate', 'DRPRate', 'FDPRate', 'BranchRate')
        ],
        # BillNo: widen from CHAR(20) to VARCHAR(20) if needed
        """DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='Stocks' AND column_name='BillNo'
                AND data_type='character'
            ) THEN
                ALTER TABLE "Stocks" ALTER COLUMN "BillNo" TYPE VARCHAR(20);
            END IF;
        END $$""",
    ]

    try:
        with connections[db_alias].cursor() as cur:
            cur.execute(ddl)
            for sql in _migrate_sql:
                try:
                    cur.execute(sql)
                except Exception:
                    pass  # column may already exist with right type
        _ENSURED_STOCK_TABLES.add(db_alias)
        logger.debug('ensure_stocks_table: table ready in %s', db_alias)
        return True
    except (OperationalError, ProgrammingError) as exc:
        logger.error('ensure_stocks_table: could not create/migrate table in %s: %s', db_alias, exc)
        return False


def flatten_multiunit_data(multiunit_json: str) -> dict:
    """
    Parse the MultiUnitManager JSON blob and return a dict of flattened
    column values ready for INSERT/UPDATE into the Stocks table.

    Expected JSON structure (list of up to 6 unit objects):
    [
        {
            "unit_name": "Pack",
            "factor": "0.1",
            "prices": {
                "base_rate": "10.00", "mrp_rate": "20.00",
                "drp_rate": "10.00", "fdp_rate": "5.00",
                "branch_rate": "2.50"
            }
        }, ...
    ]
    """
    result = {}
    if not multiunit_json:
        return result

    try:
        units = json.loads(multiunit_json) if isinstance(multiunit_json, str) else (multiunit_json or [])
    except (ValueError, TypeError):
        return result

    for i, unit in enumerate(units[:6], start=1):
        prices = unit.get('prices', {}) if isinstance(unit, dict) else {}

        def _f(key):
            v = prices.get(key, '') or ''
            try:
                return float(v) if v else None
            except (ValueError, TypeError):
                return None

        result[f'Unit{i}BaseRate']   = _f('base_rate')
        result[f'Unit{i}MRPRate']    = _f('mrp_rate')
        result[f'Unit{i}DRPRate']    = _f('drp_rate')
        result[f'Unit{i}FDPRate']    = _f('fdp_rate')
        result[f'Unit{i}BranchRate'] = _f('branch_rate')

    return result


class Stock(models.Model):
    """
    ORM representation of the Stocks table.
    managed=False — table is created via ensure_stocks_table().
    PK: ItemID (one row per item for Item Master use).
    Rate0 = Purchase Price (the six rates are configured via ChartOfCode captions).
    """
    StockID          = models.IntegerField(db_column='StockID')
    ItemID           = models.IntegerField(primary_key=True, db_column='ItemID')

    # Selling Rates — Rate0 is the purchase/base price
    Rate0            = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, default=0, db_column='Rate0')
    Rate1            = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, default=0, db_column='Rate1')
    Rate2            = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Rate2')
    Rate3            = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Rate3')
    Rate4            = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Rate4')
    Rate5            = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Rate5')
    LUCost           = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='LUCost')

    FirmID           = models.IntegerField(null=True, blank=True, db_column='FirmID')
    Vendor           = models.IntegerField(null=True, blank=True, db_column='Vendor')

    Discount         = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Discount')
    SpecialDiscount  = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='SpecialDiscount')
    PurchaseDiscount = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='PurchaseDiscount')

    PurchaseDate     = models.DateTimeField(null=True, blank=True, db_column='PurchaseDate')
    BillNo           = models.CharField(max_length=20, null=True, blank=True, db_column='BillNo')
    StockDate        = models.DateTimeField(null=True, blank=True, db_column='StockDate')

    MultiUnitData    = models.TextField(null=True, blank=True, db_column='MultiUnitData')

    Unit1BaseRate   = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit1BaseRate')
    Unit1MRPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit1MRPRate')
    Unit1DRPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit1DRPRate')
    Unit1FDPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit1FDPRate')
    Unit1BranchRate = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit1BranchRate')

    Unit2BaseRate   = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit2BaseRate')
    Unit2MRPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit2MRPRate')
    Unit2DRPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit2DRPRate')
    Unit2FDPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit2FDPRate')
    Unit2BranchRate = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit2BranchRate')

    Unit3BaseRate   = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit3BaseRate')
    Unit3MRPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit3MRPRate')
    Unit3DRPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit3DRPRate')
    Unit3FDPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit3FDPRate')
    Unit3BranchRate = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit3BranchRate')

    Unit4BaseRate   = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit4BaseRate')
    Unit4MRPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit4MRPRate')
    Unit4DRPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit4DRPRate')
    Unit4FDPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit4FDPRate')
    Unit4BranchRate = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit4BranchRate')

    Unit5BaseRate   = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit5BaseRate')
    Unit5MRPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit5MRPRate')
    Unit5DRPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit5DRPRate')
    Unit5FDPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit5FDPRate')
    Unit5BranchRate = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit5BranchRate')

    Unit6BaseRate   = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit6BaseRate')
    Unit6MRPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit6MRPRate')
    Unit6DRPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit6DRPRate')
    Unit6FDPRate    = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit6FDPRate')
    Unit6BranchRate = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit6BranchRate')

    class Meta:
        db_table = 'Stocks'
        managed  = False
