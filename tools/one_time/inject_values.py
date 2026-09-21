import re

path = 'inventory/views/item_master.py'
with open(path, 'r', encoding='utf-8') as f: code = f.read()

# We need to find every field(...) call inside build_item_master_form_config
# and inject value=d.get('<name>', '') if it doesn't have value=
def repl(m):
    full_match = m.group(0)
    name = m.group(1)
    
    # If it already has value=, leave it alone
    if 'value=' in full_match:
        return full_match
        
    # Otherwise, inject value=d.get('name', '')
    # full_match ends with ')', so we replace the last ')' with ', value=d.get('name', ''))'
    # Actually it might be better to just regex it
    # We match up to the end parenthesis, but there could be nested parenthesis like options=[...]
    return full_match

# It's safer to just do simple replacements for the known fields.
lines = code.split('\n')
in_config = False
for i, line in enumerate(lines):
    if 'def build_item_master_form_config' in line:
        in_config = True
    elif in_config and 'def ' in line:
        in_config = False
        
    if in_config and 'field(' in line:
        # Check if value= is missing
        if 'value=' not in line:
            # Extract the field name: field('FieldName', ...)
            match = re.search(r"field\(\s*['\"]([^'\"]+)['\"]", line)
            if match:
                name = match.group(1)
                # Find the closing parenthesis of the field() call.
                # Since some might have dict unpacking like {**field(...)}, we just replace the last ')'?
                # A safer approach: insert before the last ')'
                # But what if there are dicts inside? 
                pass

with open(path, 'w', encoding='utf-8') as f: f.write(code)
print('Analyzed')
