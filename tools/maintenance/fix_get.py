import re

path = 'inventory/views/item_master.py'
with open(path, 'r', encoding='utf-8') as f: code = f.read()

old_func_pattern = r'def get_item_data\(item_code\):.*?return data\s+except Exception as e:\s+logger\.error\("Error fetching item data for %s: %s", item_code, e\)\s+return \{\}'

new_func = '''def get_item_data(item_code):
    try:
        from common.middleware.database_middleware import get_customer_db
        db = get_customer_db()
        with connections[db].cursor() as cur:
            cur.execute('SELECT * FROM "InventoryItems" WHERE "ItemCode" ILIKE %s', [item_code])
            row = cur.fetchone()
            if not row:
                return {}
            cols = [d[0] for d in cur.description]
            data = dict(zip(cols, row))
            
            created_at = data.get('CreatedAt')
            if created_at:
                if hasattr(created_at, 'strftime'):
                    data['RegDate'] = created_at.strftime('%Y-%m-%d')
                else:
                    data['RegDate'] = str(created_at)[:10]
            
            resolved_id = data.get('ItemID')
            if resolved_id:
                cur.execute('SELECT * FROM "Stocks" WHERE "ItemID" = %s', [resolved_id])
                stock_row = cur.fetchone()
                if stock_row:
                    stock_cols = [d[0] for d in cur.description]
                    data.update(dict(zip(stock_cols, stock_row)))
                    data['multiunit_data'] = data.get('MultiUnitData') or ''
                    
            from datetime import date, datetime
            for k, v in data.items():
                if isinstance(v, (date, datetime)):
                    data[k] = v.strftime('%Y-%m-%d')
                elif hasattr(v, '__float__'):
                    data[k] = str(v)
            return data
    except Exception as e:
        logger.error("Error fetching item data for %s: %s", item_code, e)
        return {}'''

code = re.sub(old_func_pattern, new_func, code, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f: f.write(code)
print('Fixed get_item_data')
