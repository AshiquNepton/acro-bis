import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_project.settings')
django.setup()

from core.crud import fetch_all
from django.db import connections

def test_query():
    db_alias = 'default'  # Or whatever db is used
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
        print("Sample:", raw_rows[:2])
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    test_query()
