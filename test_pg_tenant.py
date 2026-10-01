import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_project.settings')
django.setup()

from django.db import connections

def query_tenant():
    with connections['default'].cursor() as c:
        c.execute('SELECT "DBHost", "DBName", "DBUser", "DBPassword" FROM "Tenants" LIMIT 1')
        row = c.fetchone()
        
    if not row:
        print("No tenants!")
        return
        
    print("Tenant found:", row[1])
    
    from erp_project.settings import DATABASES
    DATABASES['customer_db'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': row[1],
        'USER': row[2],
        'PASSWORD': row[3],
        'HOST': row[0],
    }
    
    from core.crud import fetch_all
    try:
        raw_rows = fetch_all('customer_db', '''
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
            print("First:", raw_rows[0])
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    query_tenant()
