import logging
from django.db import connections, OperationalError, ProgrammingError
from django.db import models

logger = logging.getLogger(__name__)

_ENSURED_ITEM_TABLES = set()


def ensure_inventory_items_table(db_alias: str, force: bool = False) -> bool:
    """
    Create the InventoryItems table + indexes in the given database alias if it
    does not already exist. Cached in memory so it executes at most once per process.

    Removed columns (now live in Stocks):
        PurchasePrice, MRP, DRP, FDP  — prices are in Stocks.Rate0–Rate5
    """
    if not force and db_alias in _ENSURED_ITEM_TABLES:
        return True

    ddl = """
        CREATE TABLE IF NOT EXISTS "InventoryItems" (
            -- Identity
            "ItemID"              INT           NOT NULL,
            "ItemCode"            VARCHAR(35)   NULL,
            "ItemName"            VARCHAR(100)  NULL,

            -- Item Group hierarchy (resolved from ItemGroups via typecodes)
            "Item"                INT           NULL,
            "ItemGroup1"          INT           NULL,
            "ItemGroup2"          INT           NULL,
            "ItemGroup3"          INT           NULL,
            "ItemGroup4"          INT           NULL,
            "ItemGroup5"          INT           NULL,

            -- Basic identifiers
            "ShortName"           VARCHAR(100)  NULL,
            "LocalName"           VARCHAR(100)  NULL,
            "ItemType"            SMALLINT      NULL,
            "StockValuation"      SMALLINT      NULL,
            "BinLocation"         VARCHAR(100)  NULL,
            "DefaultWarehouse"    SMALLINT      NULL,

            -- Tax
            "Tax"                 NUMERIC(19,4) NULL,
            "TaxGroup"            INT           NULL,
            "TaxCode"             VARCHAR(15)   NULL,

            -- Stock limits
            "MinStock"            INT           NULL,
            "MaxStock"            INT           NULL,
            "ReorderQty"          INT           NULL,
            "FixedPrice"          NUMERIC(19,4) NULL,
            "DecimalsAllowed"     SMALLINT      NULL,

            -- Codes & tracking
            "SupplierProductCode" VARCHAR(35)   NULL,
            "AssortedBarcode"     VARCHAR(100)  NULL,
            "WarrantyPeriod"      INT           NULL,

            -- Brand / Category (GroupID refs into ItemGroups)
            "BrandName"           INT           NULL,
            "CategoryName"        INT           NULL,

            -- Units of measure (GroupID refs into ItemGroups, typecode 9)
            "BaseUnit"            INT           NULL,
            "PurchaseUnit"        INT           NULL,
            "SalesUnit"           INT           NULL,

            -- Packing (GroupID ref into ItemGroups, typecode 129)
            "PackingDetails"      INT           NULL,

            -- Multi-unit conversions (up to 6 alternate UOM levels)
            "Unit1"               INT           NULL,
            "Unit1Conversion"     NUMERIC(19,4) NULL,
            "Unit1Barcode"        VARCHAR(15)   NULL,
            "Unit2"               INT           NULL,
            "Unit2Conversion"     NUMERIC(19,4) NULL,
            "Unit2Barcode"        VARCHAR(15)   NULL,
            "Unit3"               INT           NULL,
            "Unit3Conversion"     NUMERIC(19,4) NULL,
            "Unit3Barcode"        VARCHAR(15)   NULL,
            "Unit4"               INT           NULL,
            "Unit4Conversion"     NUMERIC(19,4) NULL,
            "Unit4Barcode"        VARCHAR(15)   NULL,
            "Unit5"               INT           NULL,
            "Unit5Conversion"     NUMERIC(19,4) NULL,
            "Unit5Barcode"        VARCHAR(15)   NULL,
            "Unit6"               INT           NULL,
            "Unit6Conversion"     NUMERIC(19,4) NULL,
            "Unit6Barcode"        VARCHAR(15)   NULL,

            -- Discounts (stored here; selling rates stored in Stocks.Rate0-Rate5)
            "PurDiscount"         NUMERIC(19,4) NULL,
            "Discount"            NUMERIC(19,4) NULL,
            "SPDiscount"          NUMERIC(19,4) NULL,
            "LastUnitCost"        NUMERIC(19,4) NULL,

            -- Classification / grouping (GroupID refs into ItemGroups)
            "SubGroup"            INT           NULL,
            "Category"            INT           NULL,
            "PreferredSupplier"   INT           NULL,
            "CountryOfOrigin"     INT           NULL,
            "Supplier"            INT           NULL,
            "Warehouse"           INT           NULL,
            "Company"             INT           NULL,
            "Brand"               INT           NULL,
            "Department"          INT           NULL,
            "Section"             INT           NULL,
            "Family"              INT           NULL,
            "Flavour"             INT           NULL,
            "Color"               INT           NULL,
            "Type"                INT           NULL,

            -- Product info
            "ProductDescription"  VARCHAR(250)  NULL,
            "ManufacturerPartNo"  VARCHAR(35)   NULL,
            "AltCodes"            VARCHAR(100)  NULL,

            -- Meta
            "Status"              SMALLINT      NULL DEFAULT 1,
            "CreatedAt"           TIMESTAMP     NULL DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT "PK_InventoryItems" PRIMARY KEY ("ItemID")
        );
        CREATE INDEX IF NOT EXISTS "idx_inventoryitems_itemcode"
            ON "InventoryItems" ("ItemCode");
        CREATE INDEX IF NOT EXISTS "idx_inventoryitems_itemname"
            ON "InventoryItems" ("ItemName");
        CREATE INDEX IF NOT EXISTS "idx_inventoryitems_barcode1"
            ON "InventoryItems" ("Unit1Barcode");
        CREATE INDEX IF NOT EXISTS "idx_inventoryitems_itemgroups"
            ON "InventoryItems" ("ItemGroup1", "ItemGroup2", "ItemGroup3");
        CREATE INDEX IF NOT EXISTS "idx_inventoryitems_brand"
            ON "InventoryItems" ("Brand");
        CREATE INDEX IF NOT EXISTS "idx_inventoryitems_category"
            ON "InventoryItems" ("Category");
        CREATE INDEX IF NOT EXISTS "idx_inventoryitems_status"
            ON "InventoryItems" ("Status");
        CREATE INDEX IF NOT EXISTS "idx_inventoryitems_packingdetails"
            ON "InventoryItems" ("PackingDetails");
    """

    # Incremental ALTER — adds missing columns on older DBs in one batch
    _migrate_alters = [
        # Group hierarchy columns (may be missing on very old installs)
        'ALTER TABLE "InventoryItems" ADD COLUMN IF NOT EXISTS "Item"       INT NULL',
        'ALTER TABLE "InventoryItems" ADD COLUMN IF NOT EXISTS "ItemGroup1" INT NULL',
        'ALTER TABLE "InventoryItems" ADD COLUMN IF NOT EXISTS "ItemGroup2" INT NULL',
        'ALTER TABLE "InventoryItems" ADD COLUMN IF NOT EXISTS "ItemGroup3" INT NULL',
        'ALTER TABLE "InventoryItems" ADD COLUMN IF NOT EXISTS "ItemGroup4" INT NULL',
        'ALTER TABLE "InventoryItems" ADD COLUMN IF NOT EXISTS "ItemGroup5" INT NULL',
        # Packing type
        'ALTER TABLE "InventoryItems" ADD COLUMN IF NOT EXISTS "PackingDetails" INT NULL',
        # Extra group fields
        'ALTER TABLE "InventoryItems" ADD COLUMN IF NOT EXISTS "Department"  INT NULL',
        'ALTER TABLE "InventoryItems" ADD COLUMN IF NOT EXISTS "Section"     INT NULL',
        'ALTER TABLE "InventoryItems" ADD COLUMN IF NOT EXISTS "Family"      INT NULL',
        'ALTER TABLE "InventoryItems" ADD COLUMN IF NOT EXISTS "Flavour"     INT NULL',
        'ALTER TABLE "InventoryItems" ADD COLUMN IF NOT EXISTS "Color"       INT NULL',
        'ALTER TABLE "InventoryItems" ADD COLUMN IF NOT EXISTS "Type"        INT NULL',
        'ALTER TABLE "InventoryItems" ADD COLUMN IF NOT EXISTS "Company"     INT NULL',
        'ALTER TABLE "InventoryItems" ADD COLUMN IF NOT EXISTS "CountryOfOrigin" INT NULL',
        # Widen AltCodes from old CHAR(100) → VARCHAR(100)
        """DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='InventoryItems' AND column_name='AltCodes'
                AND data_type='character'
            ) THEN
                ALTER TABLE "InventoryItems" ALTER COLUMN "AltCodes" TYPE VARCHAR(100);
            END IF;
        END $$""",
        # Widen LocalName from old CHAR(100) → VARCHAR(100)
        """DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='InventoryItems' AND column_name='LocalName'
                AND data_type='character'
            ) THEN
                ALTER TABLE "InventoryItems" ALTER COLUMN "LocalName" TYPE VARCHAR(100);
            END IF;
        END $$""",
    ]

    try:
        with connections[db_alias].cursor() as cur:
            cur.execute(ddl)
            for sql in _migrate_alters:
                try:
                    cur.execute(sql)
                except Exception:
                    pass  # column may already exist correctly
        _ENSURED_ITEM_TABLES.add(db_alias)
        logger.debug('ensure_inventory_items_table: table ready in %s', db_alias)
        return True
    except (OperationalError, ProgrammingError) as exc:
        logger.error(
            'ensure_inventory_items_table: could not create/migrate table in %s: %s',
            db_alias, exc
        )
        return False


class InventoryItem(models.Model):
    """
    ORM representation of InventoryItems table.
    managed=False — table is created via ensure_inventory_items_table().

    NOTE: Selling prices (Rate0–Rate5) are stored in the Stocks table, not here.
    """
    ItemID = models.IntegerField(primary_key=True, db_column='ItemID')
    ItemCode = models.CharField(max_length=35, null=True, blank=True, db_column='ItemCode', unique=True)
    ItemName = models.CharField(max_length=100, null=True, blank=True, db_column='ItemName')

    # Group hierarchy
    Item       = models.IntegerField(null=True, blank=True, db_column='Item')
    ItemGroup1 = models.IntegerField(null=True, blank=True, db_column='ItemGroup1')
    ItemGroup2 = models.IntegerField(null=True, blank=True, db_column='ItemGroup2')
    ItemGroup3 = models.IntegerField(null=True, blank=True, db_column='ItemGroup3')
    ItemGroup4 = models.IntegerField(null=True, blank=True, db_column='ItemGroup4')
    ItemGroup5 = models.IntegerField(null=True, blank=True, db_column='ItemGroup5')

    ShortName         = models.CharField(max_length=100, null=True, blank=True, db_column='ShortName')
    LocalName         = models.CharField(max_length=100, null=True, blank=True, db_column='LocalName')
    ItemType          = models.SmallIntegerField(null=True, blank=True, db_column='ItemType')
    StockValuation    = models.SmallIntegerField(null=True, blank=True, db_column='StockValuation')
    BinLocation       = models.CharField(max_length=100, null=True, blank=True, db_column='BinLocation')
    DefaultWarehouse  = models.SmallIntegerField(null=True, blank=True, db_column='DefaultWarehouse')

    Tax     = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Tax')
    TaxGroup = models.IntegerField(null=True, blank=True, db_column='TaxGroup')
    TaxCode  = models.CharField(max_length=15, null=True, blank=True, db_column='TaxCode')

    MinStock         = models.IntegerField(null=True, blank=True, db_column='MinStock')
    MaxStock         = models.IntegerField(null=True, blank=True, db_column='MaxStock')
    ReorderQty       = models.IntegerField(null=True, blank=True, db_column='ReorderQty')
    FixedPrice       = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='FixedPrice')
    DecimalsAllowed  = models.SmallIntegerField(null=True, blank=True, db_column='DecimalsAllowed')

    SupplierProductCode = models.CharField(max_length=35,  null=True, blank=True, db_column='SupplierProductCode')
    AssortedBarcode     = models.CharField(max_length=100, null=True, blank=True, db_column='AssortedBarcode')
    WarrantyPeriod      = models.IntegerField(null=True, blank=True, db_column='WarrantyPeriod')

    BrandName    = models.IntegerField(null=True, blank=True, db_column='BrandName')
    CategoryName = models.IntegerField(null=True, blank=True, db_column='CategoryName')

    # UOM
    BaseUnit      = models.IntegerField(null=True, blank=True, db_column='BaseUnit')
    PurchaseUnit  = models.IntegerField(null=True, blank=True, db_column='PurchaseUnit')
    SalesUnit     = models.IntegerField(null=True, blank=True, db_column='SalesUnit')
    PackingDetails = models.IntegerField(null=True, blank=True, db_column='PackingDetails')

    # Multi-unit conversions
    Unit1 = models.IntegerField(null=True, blank=True, db_column='Unit1')
    Unit1Conversion = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit1Conversion')
    Unit1Barcode = models.CharField(max_length=15, null=True, blank=True, db_column='Unit1Barcode')

    Unit2 = models.IntegerField(null=True, blank=True, db_column='Unit2')
    Unit2Conversion = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit2Conversion')
    Unit2Barcode = models.CharField(max_length=15, null=True, blank=True, db_column='Unit2Barcode')

    Unit3 = models.IntegerField(null=True, blank=True, db_column='Unit3')
    Unit3Conversion = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit3Conversion')
    Unit3Barcode = models.CharField(max_length=15, null=True, blank=True, db_column='Unit3Barcode')

    Unit4 = models.IntegerField(null=True, blank=True, db_column='Unit4')
    Unit4Conversion = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit4Conversion')
    Unit4Barcode = models.CharField(max_length=15, null=True, blank=True, db_column='Unit4Barcode')

    Unit5 = models.IntegerField(null=True, blank=True, db_column='Unit5')
    Unit5Conversion = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit5Conversion')
    Unit5Barcode = models.CharField(max_length=15, null=True, blank=True, db_column='Unit5Barcode')

    Unit6 = models.IntegerField(null=True, blank=True, db_column='Unit6')
    Unit6Conversion = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit6Conversion')
    Unit6Barcode = models.CharField(max_length=15, null=True, blank=True, db_column='Unit6Barcode')

    # Discounts
    PurDiscount  = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='PurDiscount')
    Discount     = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Discount')
    SPDiscount   = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='SPDiscount')
    LastUnitCost = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='LastUnitCost')

    # Classifications
    SubGroup          = models.IntegerField(null=True, blank=True, db_column='SubGroup')
    Category          = models.IntegerField(null=True, blank=True, db_column='Category')
    PreferredSupplier = models.IntegerField(null=True, blank=True, db_column='PreferredSupplier')
    CountryOfOrigin   = models.IntegerField(null=True, blank=True, db_column='CountryOfOrigin')
    Supplier          = models.IntegerField(null=True, blank=True, db_column='Supplier')
    Warehouse         = models.IntegerField(null=True, blank=True, db_column='Warehouse')
    Company           = models.IntegerField(null=True, blank=True, db_column='Company')
    Brand             = models.IntegerField(null=True, blank=True, db_column='Brand')
    Department        = models.IntegerField(null=True, blank=True, db_column='Department')
    Section           = models.IntegerField(null=True, blank=True, db_column='Section')
    Family            = models.IntegerField(null=True, blank=True, db_column='Family')
    Flavour           = models.IntegerField(null=True, blank=True, db_column='Flavour')
    Color             = models.IntegerField(null=True, blank=True, db_column='Color')
    Type              = models.IntegerField(null=True, blank=True, db_column='Type')

    ProductDescription = models.CharField(max_length=250, null=True, blank=True, db_column='ProductDescription')
    ManufacturerPartNo = models.CharField(max_length=35,  null=True, blank=True, db_column='ManufacturerPartNo')
    AltCodes           = models.CharField(max_length=100, null=True, blank=True, db_column='AltCodes')

    Status    = models.SmallIntegerField(null=True, blank=True, default=1, db_column='Status')
    CreatedAt = models.DateTimeField(null=True, blank=True, auto_now_add=False, db_column='CreatedAt')

    class Meta:
        db_table = 'InventoryItems'
        managed  = False
