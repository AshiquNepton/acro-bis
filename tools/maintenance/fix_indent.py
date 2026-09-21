import re

path = 'inventory/views/item_master.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if "group_ids = []" in line and "for f in ['Item'" in lines[i+1]:
        # We found the start of the block
        new_lines.append('            group_ids = []\n')
        new_lines.append("            for f in ['Item', 'ItemGroup1', 'ItemGroup2', 'ItemGroup3', 'ItemGroup4', 'ItemGroup5']:\n")
        new_lines.append('                if data.get(f):\n')
        new_lines.append('                    group_ids.append(str(data[f]))\n')
        new_lines.append('            \n')
        new_lines.append('            if group_ids:\n')
        new_lines.append('                cur.execute(\'SELECT "GroupID", "Description" FROM "ItemGroups" WHERE "GroupID" = ANY(%s::int[])\', [group_ids])\n')
        new_lines.append('                desc_map = {str(row[0]): row[1] for row in cur.fetchall()}\n')
        new_lines.append("                for f in ['Item', 'ItemGroup1', 'ItemGroup2', 'ItemGroup3', 'ItemGroup4', 'ItemGroup5']:\n")
        new_lines.append('                    if data.get(f):\n')
        new_lines.append('                        data[f + \'Text\'] = desc_map.get(str(data[f]), \'\')\n')
        skip = True
    elif skip and ("return data" in line or "except Exception as e:" in line):
        skip = False
        new_lines.append(line)
    elif not skip:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Fixed indentation")
