path = 'inventory/views/item_master.py'
with open(path, 'r', encoding='utf-8') as f: code = f.read()

old_return = """        return JsonResponse({'success': True, 'data': data, 'pk': data.get('ItemID')})"""
new_return = """        with open('debug_load.txt', 'a') as f:
            f.write(f"  success: True\\n")
            f.write(f"  keys returned: {list(data.keys())}\\n")
        return JsonResponse({'success': True, 'data': data, 'pk': data.get('ItemID')})"""
code = code.replace(old_return, new_return)

old_err = """        return JsonResponse({'success': False, 'error': 'Item not found'})"""
new_err = """        with open('debug_load.txt', 'a') as f:
            f.write(f"  success: False, error: Item not found\\n")
        return JsonResponse({'success': False, 'error': 'Item not found'})"""
code = code.replace(old_err, new_err)

with open(path, 'w', encoding='utf-8') as f: f.write(code)
print('Injected return logging')
