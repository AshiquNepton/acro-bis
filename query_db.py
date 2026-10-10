import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_project.settings')
django.setup()

from django.db import connections

try:
    with connections['default'].cursor() as cursor:
        cursor.execute("SELECT * FROM customers;")
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        for row in rows:
            print(dict(zip(columns, row)))
except Exception as e:
    print(f"Error: {e}")
