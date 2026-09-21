import re

path = 'common/urls.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

new_routes = '''    path('customer/',               customers.customer_form,   name='customer'),
    path('customer/save/',          customers.save_customer,   name='save_customer'),
    path('customer/load/',          customers.load_customer,   name='load_customer'),
    path('customer/delete/',        customers.delete_customer, name='delete_customer'),
    path('customer/lookup/',        customers.lookup_customer, name='lookup_customer'),'''

code = re.sub(r"    path\('customer/'.*?name='save_customer'\),", new_routes, code, flags=re.DOTALL)
with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print('Updated customer routes')
