import re

path = 'common/views/context_processors.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# For each section where it has:
# 'id': 'inventory', ... {'label': 'Item Master', 'url': 'inventory:item_master'},
# I will just write a function to manipulate the AST or just regex replace carefully.
# Actually, since it's just a few repeated blocks, I'll regex replace the whole thing or just write a python script to parse and modify it.

def replace_nav(code):
    # Remove 'Item Master' from 'inventory'
    code = code.replace("{'label': 'Item Master', 'url': 'inventory:item_master'},\n", "")
    code = code.replace("{'label': 'Item Master', 'url': 'inventory:item_master'},", "")
    
    # Remove 'Customers' and 'Employee / Dept' from 'masters'
    code = code.replace("{'label': 'Customers',    'url': 'common:customer'},\n", "")
    code = code.replace("{'label': 'Customers',    'url': 'common:customer'},", "")
    
    code = code.replace("{'label': 'Employee / Dept', 'url': 'common:department_form'},\n", "")
    code = code.replace("{'label': 'Employee / Dept', 'url': 'common:department_form'},", "")
    
    # In each section list, insert Registration before Settings.
    # We can just look for the Settings block and prepend the Registration block.
    
    registration_block = '''                {
                    'id': 'registration', 'label': 'Registration', 'icon': I['Note'],
                    'items': [
                        {'label': 'Item Master', 'url': 'inventory:item_master'},
                        {'label': 'Customer',    'url': 'common:customer'},
                        {'label': 'Vendor',      'url': 'common:vendor'},
                        {'label': 'Department',  'url': 'common:department_form'},
                    ]
                },
                {
                    'id': 'settings','''
    
    code = code.replace("                {\n                    'id': 'settings',", registration_block)
    return code

new_code = replace_nav(code)

# Add Customer List and Vendor List to Reports block (if it exists, like in Inventory or Financial)
# Actually, let's just find the Reports block and inject them.
reports_find = """'id': 'reports', 'label': 'Reports', 'icon': I['Note'],
                    'items': [
                        {'label': 'Stock Report', 'url': 'reports:stock_report'},"""

reports_replace = """'id': 'reports', 'label': 'Reports', 'icon': I['Note'],
                    'items': [
                        {'label': 'Stock Report', 'url': 'reports:stock_report'},
                        {'label': 'Customer List', 'url': 'reports:customer_list'},
                        {'label': 'Vendor List', 'url': 'reports:vendor_list'},"""

new_code = new_code.replace(reports_find, reports_replace)

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_code)
print("Updated context processors")
