import re

# Remove vendors from financial/urls.py
path_fin = 'financial/urls.py'
with open(path_fin, 'r', encoding='utf-8') as f: code = f.read()
code = code.replace(', vendors', '')
code = re.sub(r'# Vendor.*name=\'lookup_vendor\'\),\n', '', code, flags=re.DOTALL)
with open(path_fin, 'w', encoding='utf-8') as f: f.write(code)

# Add vendors to common/urls.py
path_com = 'common/urls.py'
with open(path_com, 'r', encoding='utf-8') as f: code = f.read()
code = code.replace('from common.views import auth, dashboard, customers, masters, settings, company_info', 'from common.views import auth, dashboard, customers, vendors, masters, settings, company_info')
vendor_routes = '''
    # Vendor
    path('vendor/',               vendors.vendor_form,   name='vendor'),
    path('vendor/save/',          vendors.save_vendor,   name='save_vendor'),
    path('vendor/load/',          vendors.load_vendor,   name='load_vendor'),
    path('vendor/delete/',        vendors.delete_vendor, name='delete_vendor'),
    path('vendor/lookup/',        vendors.lookup_vendor, name='lookup_vendor'),
'''
code = code.replace("    path('customer/lookup/',        customers.lookup_customer, name='lookup_customer'),", "    path('customer/lookup/',        customers.lookup_customer, name='lookup_customer'),\n" + vendor_routes)
with open(path_com, 'w', encoding='utf-8') as f: f.write(code)

# Fix common/views/party_master.py to remove custom icons
path_party = 'common/views/party_master.py'
with open(path_party, 'r', encoding='utf-8') as f: code = f.read()
code = code.replace("tb('Save', 'pfSave()', icon='dY\"')", "tb('Save', 'pfSave()')")
code = code.replace("tb('New', 'pfNew()', icon='d^Y')", "tb('New', 'pfNew()')")
code = code.replace("tb('Delete', 'pfDelete()', icon='dY~_')", "tb('Delete', 'pfDelete()')")
with open(path_party, 'w', encoding='utf-8') as f: f.write(code)

# Fix template URLs inside vendor_form.html
path_vendor_tpl = 'common/templates/common/masters/vendor_form.html'
with open(path_vendor_tpl, 'r', encoding='utf-8') as f: code = f.read()
code = code.replace("'financial:lookup_vendor'", "'common:lookup_vendor'")
code = code.replace("'financial:load_vendor'", "'common:load_vendor'")
code = code.replace("'financial:save_vendor'", "'common:save_vendor'")
code = code.replace("'financial:delete_vendor'", "'common:delete_vendor'")
code = code.replace("'financial/masters/vendor_form.html'", "'common/masters/vendor_form.html'")
with open(path_vendor_tpl, 'w', encoding='utf-8') as f: f.write(code)

# Fix vendor view template reference
path_vendor_view = 'common/views/vendors.py'
with open(path_vendor_view, 'r', encoding='utf-8') as f: code = f.read()
code = code.replace("'financial/masters/vendor_form.html'", "'common/masters/vendor_form.html'")
with open(path_vendor_view, 'w', encoding='utf-8') as f: f.write(code)

print("Updates completed successfully.")
