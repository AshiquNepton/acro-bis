import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_project.settings')
django.setup()

from core.crud import fetch_all
from django.db import connections

def test_query():
    # Use the tenant database directly. Since we don't have request, 
    # we can set the credentials manually if needed, but sqlite main.db
    # has a Tenant table. Let's find the first tenant.
    
    with connections['default'].cursor() as c:
        c.execute('SELECT "DBHost", "DBName", "DBUser", "DBPassword" FROM "Tenants" LIMIT 1')
        row = c.fetchone()
        
    if not row:
        print("No tenants found!")
        return
        
    from erp_project.settings import DATABASES
    DATABASES['customer_db']['HOST'] = row[0]
    DATABASES['customer_db']['NAME'] = row[1]
    DATABASES['customer_db']['USER'] = row[2]
    DATABASES['customer_db']['PASSWORD'] = row[3]
    
    db_alias = 'customer_db'
    try:
        raw_rows = fetch_all(db_alias, '''
            SELECT 
                c."AccountID",
                c."AcCode",
                c."Description",
                COALESCE(v."Contact", '') AS "Contact",
                COALESCE(v."Mobile", '') AS "Mobile",
                COALESCE(v."City", '') AS "City",
                COALESCE(v."CreditLimit", 0) AS "CreditLimit"
            FROM "ChartOfAccounts" c
            LEFT JOIN "CustomerVendor" v ON c."AccountID" = v."AccountID"
            WHERE c."MGroup" = %s
            ORDER BY c."AccountID" ASC
        ''', [36])
        print("Rows returned:", len(raw_rows))
        if raw_rows:
            print("First row:", raw_rows[0])
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    test_query()
