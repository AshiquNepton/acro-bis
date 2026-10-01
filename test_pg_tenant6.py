import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_project.settings')
django.setup()

from django.db import connections

def query_tenant():
    with connections['default'].cursor() as c:
        c.execute('SELECT "host", "db", "username", "dbpass" FROM "softwares" LIMIT 1')
        row = c.fetchone()
        
    if not row:
        print("No softwares!")
        return
        
    from erp_project.settings import DATABASES
    DATABASES['customer_db'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': row[1],
        'USER': row[2],
        'PASSWORD': row[3],
        'HOST': row[0],
        'PORT': '5432',
        'CONN_MAX_AGE': 0,
        'CONN_HEALTH_CHECKS': False,
        'OPTIONS': {},
        'TIME_ZONE': None,
        'AUTOCOMMIT': True,
    }
    
    from common.views.party_master import ensure_party_tables
    ensure_party_tables('customer_db')
    
    from core.crud import fetch_tuples
    try:
        raw_rows = fetch_tuples('customer_db', '''
            SELECT DISTINCT "MGroup" FROM "ChartOfAccounts"
        ''', [])
        print("Rows returned:", len(raw_rows))
        if raw_rows:
            print("First row:", raw_rows[0])
    except Exception as e:
        print("Error:", type(e), e)
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    query_tenant()
