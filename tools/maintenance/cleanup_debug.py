path = 'inventory/views/item_master.py'
with open(path, 'r', encoding='utf-8') as f: lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if "with open('debug_load.txt', 'a') as f:" in line:
        skip = True
        continue
    
    if skip:
        if line.strip().startswith('f.write'):
            continue
        elif line.strip().startswith('return JsonResponse({'+"'success': False, 'error': 'Item not found'})"):
            new_lines.append("                return JsonResponse({'success': False, 'error': 'Item not found'})\n")
            skip = False
            continue
        elif line.strip().startswith('return JsonResponse({'+"'success': True, 'data': data"):
            new_lines.append("        return JsonResponse({'success': True, 'data': data, 'pk': data.get('ItemID')})\n")
            skip = False
            continue
        else:
            skip = False
    new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Cleaned up debug lines")
