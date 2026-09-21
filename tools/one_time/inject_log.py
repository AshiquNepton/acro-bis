path = 'inventory/views/item_master.py'
with open(path, 'r', encoding='utf-8') as f: code = f.read()

old = """        field = request.GET.get('field', '').strip()
        val = request.GET.get('value', '').strip()"""

new = """        field = request.GET.get('field', '').strip()
        val = request.GET.get('value', '').strip()
        
        with open('debug_load.txt', 'a') as f:
            f.write(f"load_item called:\\n")
            f.write(f"  field: {field}\\n")
            f.write(f"  val: {val}\\n")
            f.write(f"  ItemCode GET: {request.GET.get('ItemCode', '')}\\n")
"""

code = code.replace(old, new)
with open(path, 'w', encoding='utf-8') as f: f.write(code)
print('Injected logging')
