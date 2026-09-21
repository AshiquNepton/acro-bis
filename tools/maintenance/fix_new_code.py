import re

path = 'inventory/views/item_master.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

old_str = """    item_code = d.get('ItemCode') or next_item_code or 'ITM-0001'
    item_name = d.get('ItemName', '')
    is_active = str(d.get('Status', '1')) == '1'"""

new_str = """    item_code = d.get('ItemCode') or next_item_code or 'ITM-0001'
    if not any(opt.get('value') == item_code for opt in item_code_options):
        item_code_options.append({'value': item_code, 'label': f"{item_code} (New)"})
    
    item_name = d.get('ItemName', '')
    is_active = str(d.get('Status', '1')) == '1'"""

code = code.replace(old_str, new_str)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Fixed missing new item code in options")
