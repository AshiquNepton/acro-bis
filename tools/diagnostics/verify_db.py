import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nepton_erp.settings')
django.setup()

from common.middleware.database_middleware import get_customer_db
from django.db import connections

try:
    db = get_customer_db()
except Exception:
    db = 'default'

print("Using DB:", db)

with connections[db].cursor() as cur:
    item_code = 'ITM-0001'
    cur.execute('SELECT * FROM "InventoryItems" WHERE "ItemCode" ILIKE %s', [item_code])
    row = cur.fetchone()
    if not row:
        print('Item not found in DB for code:', item_code)
    else:
        cols = [d[0] for d in cur.description]
        data = dict(zip(cols, row))
        print("Data loaded:", {k: data[k] for k in list(data.keys())[:5]})
