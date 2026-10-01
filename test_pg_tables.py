import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_project.settings')
django.setup()

from django.db import connections

def query_tenant():
    with connections['default'].cursor() as c:
        c.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        tables = c.fetchall()
        print("Tables:", [t[0] for t in tables])

if __name__ == '__main__':
    query_tenant()
