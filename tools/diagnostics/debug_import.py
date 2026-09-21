import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_project.settings')
django.setup()

from django.test import Client
c = Client()
# Need to login first
from common.models.auth import Accounts
# create a superuser or find one
user = Accounts.objects.first()
if user:
    c.force_login(user)
r = c.get('/inventory/import/')
print(r.status_code)
html = r.content.decode('utf-8')
with open('debug_import.html', 'w', encoding='utf-8') as f:
    f.write(html)
