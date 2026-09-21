import os, json
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nepton_erp.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import User
from inventory.views.item_master import load_item
from unittest.mock import patch

factory = RequestFactory()
request = factory.get('/inventory/item-master/load/', {'field': 'ItemCode', 'value': 'ITM-0001'})

# Mock the login_required decorator or just mock request.session and get_customer_db
with patch('inventory.views.item_master.get_customer_db', return_value='default'):
    # wait, 'default' might not be a configured db?
    pass

# Better: just call the inner function by importing connections directly
from common.middleware.database_middleware import get_customer_db
from django.db import connections

try:
    db = get_customer_db()
except:
    db = 'default' # fallback to default db in test if needed

with connections[db].cursor() as cur:
    item_code = 'ITM-0001'
    cur.execute('SELECT * FROM "InventoryItems" WHERE "ItemCode" ILIKE %s', [item_code])
    row = cur.fetchone()
    if not row:
        print('Item not found in DB')
    else:
        cols = [d[0] for d in cur.description]
        data = dict(zip(cols, row))
        print("Data loaded:", {k: data[k] for k in list(data.keys())[:5]})
