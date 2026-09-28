import re
import os

file_path = r'D:\PROJECTS\VsCode Project\ACRO-BIS\inventory\views\import_config.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

batch_func = """def inventory_upsert_batch(db_alias: str, db_rows: list, _state={"item_id": None, "a_code_num": None}):
    from django.db import connections
    import re
    
    if not db_rows: return
    
    if _state["item_id"] is None:
        with connections[db_alias].cursor() as cur:
            cur.execute('SELECT COALESCE(MAX("ItemID"), 0) FROM "InventoryItems"')
            _state["item_id"] = cur.fetchone()[0]
            cur.execute('SELECT MAX("ItemCode") FROM "InventoryItems" WHERE "ItemCode" LIKE \\'A%\\'')
            max_a = cur.fetchone()[0]
            if max_a:
                match = re.search(r'(\\d+)$', max_a)
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

"""

# Insert batch_func before register_inventory_imports
content = content.replace("def register_inventory_imports():", batch_func + "\ndef register_inventory_imports():")

# Add upsert_batch_fn
content = content.replace("'table_creator': ensure_inventory_items_table,", "'table_creator': ensure_inventory_items_table,\n        'upsert_batch_fn': inventory_upsert_batch,")

# Change required: True to required: False for ItemCode
content = content.replace("{'excel': 'Item Code',          'db_col': 'ItemCode',         'type': 'str',   'required': True}", "{'excel': 'Item Code',          'db_col': 'ItemCode',         'type': 'str',   'required': False}")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
