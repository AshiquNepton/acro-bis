import logging
from django.db import connections, OperationalError, ProgrammingError
from django.db import models

logger = logging.getLogger(__name__)

_ENSURED_ITEM_TABLES = set()


def ensure_inventory_items_table(db_alias: str, force: bool = False) -> bool:
    """
    Create the InventoryItems table + indexes in the given database alias if it does
    not already exist. Cached in memory so it executes at most once per process.
    """
    if not force and db_alias in _ENSURED_ITEM_TABLES:
        return True

    ddl = """
        CREATE TABLE IF NOT EXISTS "InventoryItems" (
            "ItemID" INT NOT NULL,
            "ItemCode" VARCHAR(35) NULL,
            "ItemName" VARCHAR(100) NULL,
            "Item" INT NULL,
            "ItemGroup1" INT NULL,
            "ItemGroup2" INT NULL,
            "ItemGroup3" INT NULL,
            "ItemGroup4" INT NULL,
            "ItemGroup5" INT NULL,
            "ShortName" VARCHAR(100) NULL,
            "LocalName" CHAR(100) NULL,
            "ItemType" SMALLINT NULL,
            "StockValuation" SMALLINT NULL,
            "BinLocation" VARCHAR(100) NULL,
            "DefaultWarehouse" SMALLINT NULL,
            "Tax" NUMERIC(19,4) NULL,
            "TaxGroup" INT NULL,
            "TaxCode" VARCHAR(15) NULL,
            "MinStock" INT NULL,
            "MaxStock" INT NULL,
            "ReorderQty" INT NULL,
            "FixedPrice" NUMERIC(19,4) NULL,
            "DecimalsAllowed" SMALLINT NULL,
            "SupplierProductCode" VARCHAR(35) NULL,
            "AssortedBarcode" VARCHAR(100) NULL,
            "WarrantyPeriod" INT NULL,
            "BrandName" INT NULL,
            "CategoryName" INT NULL,
            "BaseUnit" INT NULL,
            "PurchaseUnit" INT NULL,
            "SalesUnit" INT NULL,
            "PackingDetails" INT NULL,
            "Unit1" INT NULL,
            "Unit1Conversion" NUMERIC(19,4) NULL,
            "Unit1Barcode" VARCHAR(15) NULL,
            "Unit2" INT NULL,
            "Unit2Conversion" NUMERIC(19,4) NULL,
            "Unit2Barcode" VARCHAR(15) NULL,
            "Unit3" INT NULL,
            "Unit3Conversion" NUMERIC(19,4) NULL,
            "Unit3Barcode" VARCHAR(15) NULL,
            "Unit4" INT NULL,
            "Unit4Conversion" NUMERIC(19,4) NULL,
            "Unit4Barcode" VARCHAR(15) NULL,
            "Unit5" INT NULL,
            "Unit5Conversion" NUMERIC(19,4) NULL,
            "Unit5Barcode" VARCHAR(15) NULL,
            "Unit6" INT NULL,
            "Unit6Conversion" NUMERIC(19,4) NULL,
            "Unit6Barcode" VARCHAR(15) NULL,
            "PurDiscount" NUMERIC(19,4) NULL,
            "Discount" NUMERIC(19,4) NULL,
            "SPDiscount" NUMERIC(19,4) NULL,
            "LastUnitCost" NUMERIC(19,4) NULL,
            "PurchasePrice" NUMERIC(19,4) NULL,
            "MRP" NUMERIC(19,4) NULL,
            "DRP" NUMERIC(19,4) NULL,
            "FDP" NUMERIC(19,4) NULL,
            "SubGroup" INT NULL,
            "Category" INT NULL,
            "PreferredSupplier" INT NULL,
            "CountryOfOrigin" INT NULL,
            "Supplier" INT NULL,
            "Warehouse" INT NULL,
            "Company" INT NULL,
            "Brand" INT NULL,
            "Department" INT NULL,
            "Section" INT NULL,
            "Family" INT NULL,
            "Flavour" INT NULL,
            "Color" INT NULL,
            "Type" INT NULL,
            "ProductDescription" VARCHAR(250) NULL,
            "ManufacturerPartNo" VARCHAR(35) NULL,
            "AltCodes" CHAR(100) NULL,
            "Status" SMALLINT NULL DEFAULT 1,
            "CreatedAt" TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "PK_InventoryItems" PRIMARY KEY ("ItemID")
        );
        CREATE INDEX IF NOT EXISTS "idx_inventoryitems_itemcode" ON "InventoryItems" ("ItemCode");
        CREATE INDEX IF NOT EXISTS "idx_inventoryitems_itemname" ON "InventoryItems" ("ItemName");
        CREATE INDEX IF NOT EXISTS "idx_inventoryitems_barcode1" ON "InventoryItems" ("Unit1Barcode");
        CREATE INDEX IF NOT EXISTS "idx_inventoryitems_itemgroups" ON "InventoryItems" ("ItemGroup1", "ItemGroup2", "ItemGroup3");
        CREATE INDEX IF NOT EXISTS "idx_inventoryitems_brand" ON "InventoryItems" ("Brand");
        CREATE INDEX IF NOT EXISTS "idx_inventoryitems_category" ON "InventoryItems" ("Category");
    """

    try:
        with connections[db_alias].cursor() as cur:
            cur.execute(ddl)
            # Ensure Item and ItemGroup1..5 columns exist for older DBs in a single statement
            try:
                cur.execute('''
                    ALTER TABLE "InventoryItems"
                    ADD COLUMN IF NOT EXISTS "Item" INT,
                    ADD COLUMN IF NOT EXISTS "ItemGroup1" INT,
                    ADD COLUMN IF NOT EXISTS "ItemGroup2" INT,
                    ADD COLUMN IF NOT EXISTS "ItemGroup3" INT,
                    ADD COLUMN IF NOT EXISTS "ItemGroup4" INT,
                    ADD COLUMN IF NOT EXISTS "ItemGroup5" INT
                ''')
            except Exception:
                pass
        _ENSURED_ITEM_TABLES.add(db_alias)
        logger.debug('ensure_inventory_items_table: table ready in %s', db_alias)
        return True
    except (OperationalError, ProgrammingError) as exc:
        logger.error(
            'ensure_inventory_items_table: could not create table in %s: %s',
            db_alias, exc
        )
        return False


class InventoryItem(models.Model):
    """
    Model for InventoryItems table
    Managed=False as it lives in customer specific databases
    """
    ItemID = models.IntegerField(primary_key=True, db_column='ItemID')
    ItemCode = models.CharField(max_length=35, null=True, blank=True, db_column='ItemCode', unique=True)
    ItemName = models.CharField(max_length=100, null=True, blank=True, db_column='ItemName')
    
    # Groups
    Item = models.IntegerField(null=True, blank=True, db_column='Item')
    ItemGroup1 = models.IntegerField(null=True, blank=True, db_column='ItemGroup1')
    ItemGroup2 = models.IntegerField(null=True, blank=True, db_column='ItemGroup2')
    ItemGroup3 = models.IntegerField(null=True, blank=True, db_column='ItemGroup3')
    ItemGroup4 = models.IntegerField(null=True, blank=True, db_column='ItemGroup4')
    ItemGroup5 = models.IntegerField(null=True, blank=True, db_column='ItemGroup5')
    
    ShortName = models.CharField(max_length=60, null=True, blank=True, db_column='ShortName')
    LocalName = models.CharField(max_length=50, null=True, blank=True, db_column='LocalName')
    ItemType = models.SmallIntegerField(null=True, blank=True, db_column='Item Type') # Space in name handled by db_column
    
    StockValuation = models.SmallIntegerField(null=True, blank=True, db_column='StockValuation')
    BinLocation = models.CharField(max_length=100, null=True, blank=True, db_column='BinLocation')
    DefaultWarehouse = models.SmallIntegerField(null=True, blank=True, db_column='DefaultWarehouse')
    
    # Tax
    Tax = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Tax')
    TaxGroup = models.IntegerField(null=True, blank=True, db_column='TaxGroup')
    TaxCode = models.CharField(max_length=15, null=True, blank=True, db_column='TaxCode')
    
    # Stock Limits
    MinStock = models.IntegerField(null=True, blank=True, db_column='MinStock')
    MaxStock = models.IntegerField(null=True, blank=True, db_column='MaxStock')
    ReorderQty = models.IntegerField(null=True, blank=True, db_column='ReorderQty')
    FixedPrice = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='FixedPrice')
    DecimalsAllowed = models.SmallIntegerField(null=True, blank=True, db_column='DecimalsAllowed')
    
    SupplierProductCode = models.IntegerField(null=True, blank=True, db_column='SupplierProductCode')
    AssortedBarcode = models.IntegerField(null=True, blank=True, db_column='AssortedBarcode')
    WarrantyPeriod = models.IntegerField(null=True, blank=True, db_column='WarrantyPeriod')
    BrandName = models.CharField(max_length=35, null=True, blank=True, db_column='BrandName')
    CategoryName = models.CharField(max_length=35, null=True, blank=True, db_column='CategoryName')
    
    # Units
    BaseUnit = models.IntegerField(null=True, blank=True, db_column='BaseUnit')
    PurchaseUnit = models.IntegerField(null=True, blank=True, db_column='PurchaseUnit')
    SalesUnit = models.IntegerField(null=True, blank=True, db_column='SalesUnit')
    PackingDetails = models.IntegerField(null=True, blank=True, db_column='PackingDetails')
    
    Unit1 = models.IntegerField(null=True, blank=True, db_column='Unit1')
    Unit1Conversion = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit1Conversion')
    Unit1Barcode = models.CharField(max_length=60, null=True, blank=True, db_column='Unit1Barcode')
    
    Unit2 = models.IntegerField(null=True, blank=True, db_column='Unit2')
    Unit2Conversion = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit2Conversion')
    Unit2Barcode = models.CharField(max_length=60, null=True, blank=True, db_column='Unit2Barcode')
    
    Unit3 = models.IntegerField(null=True, blank=True, db_column='Unit3')
    Unit3Conversion = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit3Conversion')
    Unit3Barcode = models.CharField(max_length=60, null=True, blank=True, db_column='Unit3Barcode')
    
    Unit4 = models.IntegerField(null=True, blank=True, db_column='Unit4')
    Unit4Conversion = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit4Conversion')
    Unit4Barcode = models.CharField(max_length=60, null=True, blank=True, db_column='Unit4Barcode')
    
    Unit5 = models.IntegerField(null=True, blank=True, db_column='Unit5')
    Unit5Conversion = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit5Conversion')
    Unit5Barcode = models.CharField(max_length=60, null=True, blank=True, db_column='Unit5Barcode')
    
    Unit6 = models.IntegerField(null=True, blank=True, db_column='Unit6')
    Unit6Conversion = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Unit6Conversion')
    Unit6Barcode = models.CharField(max_length=60, null=True, blank=True, db_column='Unit6Barcode')
    
    # Discounts
    PurDiscount  = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='PurDiscount')
    Discount     = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='Discount')
    SPDiscount   = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='SPDiscount')
    LastUnitCost = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='LastUnitCost')

    # Benchmark Prices
    PurchasePrice = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='PurchasePrice')
    MRP           = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='MRP')
    DRP           = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='DRP')
    FDP           = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, db_column='FDP')
    
    # Classifications
    SubGroup = models.IntegerField(null=True, blank=True, db_column='SubGroup')
    Category = models.IntegerField(null=True, blank=True, db_column='Category')
    PreferredSupplier = models.IntegerField(null=True, blank=True, db_column='PreferredSupplier')
    CountryOfOrigin = models.IntegerField(null=True, blank=True, db_column='CountryOfOrigin')
    Supplier = models.IntegerField(null=True, blank=True, db_column='Supplier')
    Warehouse = models.IntegerField(null=True, blank=True, db_column='Warehouse')
    Company = models.IntegerField(null=True, blank=True, db_column='Company')
    Brand = models.IntegerField(null=True, blank=True, db_column='Brand')
    Department = models.IntegerField(null=True, blank=True, db_column='Department')
    Section = models.IntegerField(null=True, blank=True, db_column='Section')
    Family = models.IntegerField(null=True, blank=True, db_column='Family')
    Flavour = models.IntegerField(null=True, blank=True, db_column='Flavour')
    Color = models.IntegerField(null=True, blank=True, db_column='Color')
    Type = models.IntegerField(null=True, blank=True, db_column='Type')
    
    # Details
    ProductDescription = models.CharField(max_length=250, null=True, blank=True, db_column='ProductDescription ') # Has trailing space in spec
    ManufacturerPartNo = models.CharField(max_length=35, null=True, blank=True, db_column='ManufacturerPartNo')
    AltCodes = models.CharField(max_length=255, null=True, blank=True, db_column='AltCodes')

    class Meta:
        db_table = 'InventoryItems'
        managed = False
