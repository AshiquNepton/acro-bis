import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_project.settings')
django.setup()

from django.db import connections
from core.crud import fetch_all

def test_query():
    db = 'default'
    with connections[db].cursor() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS "ChartOfAccountsTest" (
                "AccountID" INTEGER,
                "MGroup" INTEGER,
                "AcCode" VARCHAR(50),
                "Description" VARCHAR(50)
            )
        """)
        c.execute('DELETE FROM "ChartOfAccountsTest"')
        c.execute('INSERT INTO "ChartOfAccountsTest" ("AccountID", "MGroup", "AcCode", "Description") VALUES (1, 36, \'CUST-1\', \'Test\')')
        
    rows = fetch_all(db, 'SELECT c."AccountID", c."AcCode" FROM "ChartOfAccountsTest" c')
    print("Columns returned:", rows[0].keys())
    
    with connections[db].cursor() as c:
        c.execute('DROP TABLE "ChartOfAccountsTest"')

if __name__ == '__main__':
    test_query()
