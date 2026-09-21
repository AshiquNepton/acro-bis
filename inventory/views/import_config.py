"""
Inventory import type registrations.
Call register_inventory_imports() once (from inventory/views/import_view.py).
"""
from common.middleware.database_middleware import get_customer_db
from common.views.import_excel import register_import_type
from inventory.models.item import ensure_inventory_items_table

def register_inventory_imports():
    """Idempotent - safe to call on every request."""
    register_import_type('inventory', {
        'label'        : 'Inventory Items',
        'table'        : 'InventoryItems',
        'pk_col'       : 'ItemCode',  # Unique key for updates/inserts
        'db_alias_fn'  : get_customer_db,
        'table_creator': ensure_inventory_items_table,
        'columns'      : [
            {'excel': 'Item Code',          'db_col': 'ItemCode',         'type': 'str',   'required': True},
            {'excel': 'Item Name',          'db_col': 'ItemName',         'type': 'str',   'required': True},
            
            # ItemGroup lookup fields
            {'excel': 'Item',               'db_col': 'Item',             'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 29},
            {'excel': 'Group 1',            'db_col': 'ItemGroup1',       'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 1},
            {'excel': 'Group 2',            'db_col': 'ItemGroup2',       'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 30},
            {'excel': 'Group 3',            'db_col': 'ItemGroup3',       'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 31},
            {'excel': 'Group 4',            'db_col': 'ItemGroup4',       'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 201},
            {'excel': 'Group 5',            'db_col': 'ItemGroup5',       'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 202},
            
            {'excel': 'Type',               'db_col': 'ItemType',         'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 2},
            {'excel': 'Brand',              'db_col': 'BrandName',        'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 7},
            {'excel': 'Category',           'db_col': 'CategoryName',     'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 16},
            {'excel': 'SubGroup',           'db_col': 'SubGroup',         'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 124},
            {'excel': 'Family',             'db_col': 'Family',           'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 4},
            {'excel': 'Color',              'db_col': 'Color',            'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 130},
            {'excel': 'Flavour',            'db_col': 'Flavour',          'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 131},
            
            {'excel': 'Base Unit',          'db_col': 'BaseUnit',         'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 9},
            {'excel': 'Sales Unit',         'db_col': 'SalesUnit',        'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 9},
            {'excel': 'Purchase Unit',      'db_col': 'PurchaseUnit',     'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 9},
            
            # Plain fields
            {'excel': 'Short Name',         'db_col': 'ShortName',        'type': 'str',   'required': False},
            {'excel': 'Local Name',         'db_col': 'LocalName',        'type': 'str',   'required': False},
            {'excel': 'Description',        'db_col': 'ProductDescription','type': 'str',  'required': False},
            {'excel': 'Bin Location',       'db_col': 'BinLocation',      'type': 'str',   'required': False},
            {'excel': 'Tax Code',           'db_col': 'TaxCode',          'type': 'str',   'required': False},
            {'excel': 'Supplier Code',      'db_col': 'SupplierProductCode','type': 'str', 'required': False},
            {'excel': 'Barcode',            'db_col': 'AssortedBarcode',  'type': 'str',   'required': False},
            
            # Numerics
            {'excel': 'Min Stock',          'db_col': 'MinStock',         'type': 'int',   'required': False},
            {'excel': 'Max Stock',          'db_col': 'MaxStock',         'type': 'int',   'required': False},
            {'excel': 'Reorder Qty',        'db_col': 'ReorderQty',       'type': 'int',   'required': False},
            {'excel': 'Warranty (Months)',  'db_col': 'WarrantyPeriod',   'type': 'int',   'required': False},
            
            {'excel': 'Purchase Price',     'db_col': 'PurchasePrice',    'type': 'float', 'required': False},
            {'excel': 'MRP',                'db_col': 'MRP',              'type': 'float', 'required': False},
            {'excel': 'DRP',                'db_col': 'DRP',              'type': 'float', 'required': False},
            {'excel': 'FDP',                'db_col': 'FDP',              'type': 'float', 'required': False},
            {'excel': 'Last Unit Cost',     'db_col': 'LastUnitCost',     'type': 'float', 'required': False},
            {'excel': 'Discount %',         'db_col': 'Discount',         'type': 'float', 'required': False},
            {'excel': 'SP Discount %',      'db_col': 'SPDiscount',       'type': 'float', 'required': False},
            {'excel': 'Pur Discount %',     'db_col': 'PurDiscount',      'type': 'float', 'required': False},
            {'excel': 'Tax %',              'db_col': 'Tax',              'type': 'float', 'required': False},
        ],
    })
