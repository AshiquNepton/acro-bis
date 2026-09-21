import re

path = 'inventory/views/item_master.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update build_item_master_form_config signature
code = code.replace(
    "def build_item_master_form_config(item_data=None, next_item_code='ITM-0001', options_map=None):",
    "def build_item_master_form_config(item_data=None, next_item_code='ITM-0001', options_map=None, item_code_options=None):\n    item_code_options = item_code_options or []"
)

# 2. Update ItemCode field definition
old_item_code = """        {
            'name': 'ItemCode',
            'label': 'Item Code',
            'type': '1',
            'width': '140px',
            'required': True,
            'lookup_btn': True,
            'value': item_code,
        },"""

new_item_code = """        {
            'name': 'ItemCode',
            'label': 'Item Code',
            'type': '19',
            'width': '140px',
            'required': True,
            'lookup_btn': True,
            'value': item_code,
            'options': item_code_options,
            'onchange': 'pfLookupNow(this.form.id)'
        },"""

code = code.replace(old_item_code, new_item_code)

# 3. Update item_master_view to fetch item_code_options
view_pattern = r"def item_master_view\(request\):.*?all_needed_categories = "
new_view_code = """def item_master_view(request):
    # Fetch all item codes for the custom dropdown
    item_code_options = []
    try:
        from common.middleware.database_middleware import get_customer_db
        db = get_customer_db()
        with connections[db].cursor() as cur:
            cur.execute('SELECT "ItemCode", "ItemName" FROM "InventoryItems" ORDER BY "ItemCode"')
            for row in cur.fetchall():
                item_code_options.append({'value': row[0], 'label': f"{row[0]} - {row[1]}"})
    except Exception as e:
        logger.error("Error fetching item codes: %s", e)

    # 1. Batch fetch ALL needed ItemGroups in 1 single round-trip:
    all_needed_categories = """

code = re.sub(view_pattern, new_view_code, code, flags=re.DOTALL)

# 4. Pass item_code_options to build_item_master_form_config
config_call = """    cfg = build_item_master_form_config(
        item_data=item_data, 
        next_item_code=next_code,
        options_map=options_map
    )"""

new_config_call = """    cfg = build_item_master_form_config(
        item_data=item_data, 
        next_item_code=next_code,
        options_map=options_map,
        item_code_options=item_code_options
    )"""

code = code.replace(config_call, new_config_call)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated ItemCode to use custom dropdown")
