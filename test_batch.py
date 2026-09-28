import os, django, psycopg2
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_project.settings')
django.setup()
from django.db import connections

def test_upsert_batch():
    from inventory.views.import_config import inventory_upsert_batch
    db_rows = [
        {'ItemName': 'Batch Test 1'},
        {'ItemName': 'Batch Test 2'}
    ]
    connections['customer_db'].settings_dict['PASSWORD'] = 'Nepton12101210'
    inventory_upsert_batch('customer_db', db_rows)
    print("Done")
    
if __name__ == '__main__':
    # test_upsert_batch()
    pass
