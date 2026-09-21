import re

path = 'inventory/views/item_master.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    'ORDER BY "ItemID" DESC LIMIT 50 LIMIT 30',
    'ORDER BY "ItemCode" LIMIT 30'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Fixed syntax error")
