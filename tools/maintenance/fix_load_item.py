import re

path = 'inventory/views/item_master.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Find the end of load_item before return JsonResponse({'success': True, 'data': data...
pattern = r'(for k, v in data\.items\(\):\s*if isinstance\(v, \(date, datetime\)\):\s*data\[k\] = v\.strftime\(\'%Y-%m-%d\'\)\s*elif hasattr\(v, \'__float__\'\):\s*data\[k\] = str\(v\)\s*)(return JsonResponse\(\{\'success\': True, \'data\': data, \'pk\': data\.get\(\'ItemID\'\)\}\))'

replacement = r'''\1
        # Also resolve the ItemGroups texts for the split modal!
        group_ids = []
        for f in ['Item', 'ItemGroup1', 'ItemGroup2', 'ItemGroup3', 'ItemGroup4', 'ItemGroup5']:
            if data.get(f):
                group_ids.append(str(data[f]))
                
        if group_ids:
            with connections[db].cursor() as cur2:
                cur2.execute('SELECT "GroupID", "Description" FROM "ItemGroups" WHERE "GroupID" = ANY(%s::int[])', [group_ids])
                desc_map = {str(row[0]): row[1] for row in cur2.fetchall()}
                for f in ['Item', 'ItemGroup1', 'ItemGroup2', 'ItemGroup3', 'ItemGroup4', 'ItemGroup5']:
                    if data.get(f):
                        data[f + 'Text'] = desc_map.get(str(data[f]), '')

        \2'''

new_code = re.sub(pattern, replacement, code, flags=re.DOTALL)
with open(path, 'w', encoding='utf-8') as f:
    f.write(new_code)
print("Injected ItemText logic into load_item")
