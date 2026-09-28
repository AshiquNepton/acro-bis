import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_project.settings')
django.setup()

from django.test import RequestFactory
from common.views.import_excel import import_excel_process
from common.middleware.database_middleware import get_customer_db

import json
from django.contrib.sessions.backends.db import SessionStore

print("Starting test...")

request = RequestFactory().post(
    '/inventory/import/process/',
    data=json.dumps({
        'import_type': 'inventory',
        'rows': [
            {'Item Name': 'Test Item 1', 'Item Code': ''},
            {'Item Name': 'Test Item 2', 'Item Code': ''}
        ]
    }),
    content_type='application/json'
)

request.session = SessionStore()
request.session['is_authenticated'] = True

response = import_excel_process(request)
print("Response:", response.status_code)
print("Body:", response.content)
