"""
Inventory import type registrations.
Call register_inventory_imports() once (from inventory/views/import_view.py).
"""
from common.middleware.database_middleware import get_customer_db
from common.views.import_excel import register_import_type
from inventory.models.item import ensure_inventory_items_table

def inventory_upsert_batch(db_alias: str, db_rows: list, _state={"item_id": None, "a_code_num": None}):
    from django.db import connections
    import re
    
    if not db_rows: return
    
    if _state["item_id"] is None:
        with connections[db_alias].cursor() as cur:
            cur.execute('SELECT COALESCE(MAX("ItemID"), 0) FROM "InventoryItems"')
            _state["item_id"] = cur.fetchone()[0]
            cur.execute('SELECT MAX("ItemCode") FROM "InventoryItems" WHERE "ItemCode" LIKE \'A%\'')
            max_a = cur.fetchone()[0]
            if max_a:
                match = re.search(r'(\d+)$', max_a)
                _state["a_code_num"] = int(match.group(1)) if match else 0
            else:
                _state["a_code_num"] = 0
                
    provided_codes = [r.get('ItemCode') for r in db_rows if r.get('ItemCode')]
    existing = {}
    if provided_codes:
        with connections[db_alias].cursor() as cur:
            cur.execute('SELECT "ItemCode", "ItemID" FROM "InventoryItems" WHERE "ItemCode" = ANY(%s)', [provided_codes])
            existing = dict(cur.fetchall())
            
    from inventory.models.stock import ensure_stocks_table
    ensure_stocks_table(db_alias)
    
    sql_statements = []
    sql_params = []
    
    stocks_mapping = {
        'PurchasePrice': 'Rate0', 'MRP': 'Rate1', 'DRP': 'Rate2', 'FDP': 'Rate3',
        'LastUnitCost': 'LUCost', 'Discount': 'Discount', 'PurDiscount': 'PurchaseDiscount',
        'SPDiscount': 'SpecialDiscount',
    }
    
    q = lambda c: f'"{c}"'
    
    for db_row in db_rows:
        item_code = db_row.get('ItemCode')
        if not item_code:
            _state["a_code_num"] += 1
            item_code = f"A{_state['a_code_num']:04d}"
            db_row['ItemCode'] = item_code
            
        pk_val = item_code
        exists = item_code in existing
        item_id = existing[item_code] if exists else None
        
        if not exists:
            _state["item_id"] += 1
            item_id = _state["item_id"]
            existing[item_code] = item_id
            
        db_row['ItemID'] = item_id
        
        stock_vals = {}
        for inv_col, st_col in stocks_mapping.items():
            if inv_col in db_row:
                stock_vals[st_col] = db_row.pop(inv_col)
                
        cols = [c for c, v in db_row.items() if v is not None]
        vals = [db_row[c] for c in cols]
        
        if exists:
            update_cols = [c for c in cols if c not in ('ItemCode', 'ItemID')]
            if update_cols:
                set_clause = ', '.join(f'{q(c)} = %s' for c in update_cols)
                sql_statements.append(f'UPDATE "InventoryItems" SET {set_clause} WHERE "ItemCode" = %s;')
                sql_params.extend([db_row[c] for c in update_cols] + [pk_val])
        else:
            col_clause = ', '.join(q(c) for c in cols)
            val_clause = ', '.join('%s' for _ in cols)
            sql_statements.append(f'INSERT INTO "InventoryItems" ({col_clause}) VALUES ({val_clause});')
            sql_params.extend(vals)
            
        if stock_vals:
            stock_cols = [c for c, v in stock_vals.items() if v is not None]
            if stock_cols:
                stock_set_clause = ', '.join(f'{q(c)} = %s' for c in stock_cols)
                sql_statements.append(
                    f'UPDATE "Stocks" SET {stock_set_clause} WHERE "ItemID" = %s;'
                    f'INSERT INTO "Stocks" ("ItemID", {", ".join(q(c) for c in stock_cols)}) '
                    f'SELECT %s, {", ".join("%s" for c in stock_cols)} '
                    f'WHERE NOT EXISTS (SELECT 1 FROM "Stocks" WHERE "ItemID" = %s);'
                )
                sql_params.extend([stock_vals[c] for c in stock_cols] + [item_id])
                sql_params.extend([item_id] + [stock_vals[c] for c in stock_cols] + [item_id])
                
    if sql_statements:
        with connections[db_alias].cursor() as cur:
            cur.execute(' '.join(sql_statements), sql_params)


def register_inventory_imports():
    """Idempotent - safe to call on every request."""
    register_import_type('inventory', {
        'label'        : 'Inventory Items',
        'table'        : 'InventoryItems',
        'pk_col'       : 'ItemCode',  # Unique key for updates/inserts
        'db_alias_fn'  : get_customer_db,
        'table_creator': ensure_inventory_items_table,
        'upsert_batch_fn': inventory_upsert_batch,
        'columns'      : [
            {'excel': 'Item Code',          'db_col': 'ItemCode',         'type': 'str',   'required': False},
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
