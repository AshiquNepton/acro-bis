import re

path = 'inventory/templates/inventory/item_master_form.html'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    "lookupUrl        : \"{% url 'inventory:item_master_lookup' %}\",",
    "lookupUrl        : \"{% url 'inventory:item_master_load' %}\","
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Fixed lookupUrl")
