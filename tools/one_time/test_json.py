import os, json, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nepton_erp.settings')
django.setup()

from inventory.views.item_master import get_item_data
from django.core.serializers.json import DjangoJSONEncoder

try:
    data = get_item_data('ITM-0001')
    json.dumps(data, cls=DjangoJSONEncoder)
    print("Serialization OK")
except Exception as e:
    print("Serialization FAILED:", repr(e))
