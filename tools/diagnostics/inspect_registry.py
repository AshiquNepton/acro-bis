import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_project.settings')
django.setup()

from inventory.views.import_view import register_inventory_imports, register_employee_imports, get_import_types

register_inventory_imports()
register_employee_imports()
types = get_import_types()
print("Registered types:", types.keys())
