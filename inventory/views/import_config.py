"""
Inventory import type registrations.
Call register_inventory_imports() once.
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
    register_import_type('inventory', {
        'label'        : 'Inventory Items',
        'table'        : 'InventoryItems',
        'pk_col'       : 'ItemCode',
        'db_alias_fn'  : get_customer_db,
        'table_creator': ensure_inventory_items_table,
        'upsert_batch_fn': inventory_upsert_batch,
        'columns': [
            {'excel': 'Item Code',          'db': 'ItemCode',         'type': 'str', 'required': False},
            {'excel': 'Item Name',          'db': 'ItemName',         'type': 'str', 'required': True},
            {'excel': 'Item Category',      'db': 'Category',         'type': 'int', 'required': False},
            
            {'excel': 'Item',               'db': 'Item',             'type': 'str', 'required': False, 'itemgroup_col': True, 'category_id': 7},
            {'excel': 'Item Group 1',       'db': 'ItemGroup1',       'type': 'str', 'required': False, 'itemgroup_col': True, 'category_id': 8},
            {'excel': 'Item Group 2',       'db': 'ItemGroup2',       'type': 'str', 'required': False, 'itemgroup_col': True, 'category_id': 9},
            {'excel': 'Item Group 3',       'db': 'ItemGroup3',       'type': 'str', 'required': False, 'itemgroup_col': True, 'category_id': 10},
            {'excel': 'Item Group 4',       'db': 'ItemGroup4',       'type': 'str', 'required': False, 'itemgroup_col': True, 'category_id': 11},
            {'excel': 'Item Group 5',       'db': 'ItemGroup5',       'type': 'str', 'required': False, 'itemgroup_col': True, 'category_id': 12},

            {'excel': 'Short Name',         'db': 'ShortName',        'type': 'str', 'required': False},
            {'excel': 'Local Name',         'db': 'LocalName',        'type': 'str', 'required': False},
            {'excel': 'Item Type',          'db': 'ItemType',         'type': 'int', 'required': False},
            {'excel': 'Stock Valuation',    'db': 'StockValuation',   'type': 'int', 'required': False},
            {'excel': 'Bin Location',       'db': 'BinLocation',      'type': 'str', 'required': False},
            {'excel': 'Default Warehouse',  'db': 'DefaultWarehouse', 'type': 'int', 'required': False},

            {'excel': 'Purchase Price',     'db': 'PurchasePrice',    'type': 'float', 'required': False},
            {'excel': 'MRP',                'db': 'MRP',              'type': 'float', 'required': False},
            {'excel': 'DRP',                'db': 'DRP',              'type': 'float', 'required': False},
            {'excel': 'FDP',                'db': 'FDP',              'type': 'float', 'required': False},
            {'excel': 'Discount',           'db': 'Discount',         'type': 'float', 'required': False},
            {'excel': 'Purchase Discount',  'db': 'PurDiscount',      'type': 'float', 'required': False},
            {'excel': 'Special Discount',   'db': 'SPDiscount',       'type': 'float', 'required': False},
            {'excel': 'Last Unit Cost',     'db': 'LastUnitCost',     'type': 'float', 'required': False},

            {'excel': 'Base Unit',          'db': 'BaseUnit',         'type': 'str', 'required': False, 'itemgroup_col': True, 'category_id': 13},
            {'excel': 'Purchase Unit',      'db': 'PurchaseUnit',     'type': 'str', 'required': False, 'itemgroup_col': True, 'category_id': 14},
            {'excel': 'Sales Unit',         'db': 'SalesUnit',        'type': 'str', 'required': False, 'itemgroup_col': True, 'category_id': 15},

            {'excel': 'Tax',                'db': 'Tax',              'type': 'float', 'required': False},
            {'excel': 'Tax Group',          'db': 'TaxGroup',         'type': 'int',   'required': False},
            {'excel': 'Tax Code',           'db': 'TaxCode',          'type': 'str',   'required': False},

            {'excel': 'Minimum Qty',        'db': 'MinQty',           'type': 'float', 'required': False},
            {'excel': 'Maximum Qty',        'db': 'MaxQty',           'type': 'float', 'required': False},
            {'excel': 'Reorder Qty',        'db': 'ReOrderQty',       'type': 'float', 'required': False},
            {'excel': 'Economic Order Qty', 'db': 'EconOrderQty',     'type': 'float', 'required': False},
            
            {'excel': 'Multi Unit Data',    'db': 'MultiUnitData',    'type': 'str',   'required': False},

            {'excel': 'Brand',              'db': 'Brand',            'type': 'str',   'required': False, 'itemgroup_col': True, 'category_id': 1},
            {'excel': 'Manufacturer',       'db': 'Manufacturer',     'type': 'str',   'required': False, 'itemgroup_col': True, 'category_id': 5},
            {'excel': 'Country of Origin',  'db': 'CountryOfOrigin',  'type': 'str',   'required': False, 'itemgroup_col': True, 'category_id': 6},
            {'excel': 'Color',              'db': 'Color',            'type': 'str',   'required': False, 'itemgroup_col': True, 'category_id': 2},
            {'excel': 'Size',               'db': 'Size',             'type': 'str',   'required': False, 'itemgroup_col': True, 'category_id': 3},
            {'excel': 'Style',              'db': 'Style',            'type': 'str',   'required': False, 'itemgroup_col': True, 'category_id': 4},
            {'excel': 'Warranty',           'db': 'Warranty',         'type': 'str',   'required': False, 'itemgroup_col': True, 'category_id': 20},
            
            {'excel': 'Length',             'db': 'Length',           'type': 'float', 'required': False},
            {'excel': 'Width',              'db': 'Width',            'type': 'float', 'required': False},
            {'excel': 'Height',             'db': 'Height',           'type': 'float', 'required': False},
            {'excel': 'Weight',             'db': 'Weight',           'type': 'float', 'required': False},
            {'excel': 'Volume',             'db': 'Volume',           'type': 'float', 'required': False},

            {'excel': 'Substitute Item 1',  'db': 'SubstituteItem1',  'type': 'str',   'required': False},
            {'excel': 'Substitute Item 2',  'db': 'SubstituteItem2',  'type': 'str',   'required': False},
            {'excel': 'Related Item 1',     'db': 'RelatedItem1',     'type': 'str',   'required': False},
            {'excel': 'Related Item 2',     'db': 'RelatedItem2',     'type': 'str',   'required': False},

            {'excel': 'Status',             'db': 'Status',           'type': 'int',   'required': False},
            {'excel': 'Notes',              'db': 'Notes',            'type': 'str',   'required': False},
        ]
    })
