import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_project.settings')
django.setup()

from django.db import connections

try:
    with connections['customer_db'].cursor() as cur:
        cur.execute('SELECT "ItemCode", "ItemName", "Item", "ItemGroup1", "ItemGroup2", "ItemGroup3" FROM "InventoryItems" ORDER BY "ItemID" DESC LIMIT 5')
        rows = cur.fetchall()
        for r in rows:
            print(r)
except Exception as e:
    print(e)
