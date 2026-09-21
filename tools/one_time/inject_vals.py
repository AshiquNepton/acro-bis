import re

path = 'inventory/views/item_master.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_config = False

for line in lines:
    if 'def build_item_master_form_config' in line:
        in_config = True
    elif in_config and line.startswith('def '):
        in_config = False
        
    if in_config:
        # Match field('Name', ...)
        # We need to make sure we don't inject value= if it already has value=
        # And we don't inject for type 'section_hdr' or 'photo' or 'list_modal'
        # Actually, if we just inject value=d.get('Name', '') if 'value=' not in line, that's good enough.
        
        # Regex to find field('FieldName', ...)
        match = re.search(r"field\(\s*['\"]([^'\"]+)['\"]", line)
        if match and 'value=' not in line:
            name = match.group(1)
            # Find the matching closing parenthesis for this field() call
            # This is tricky with regex, so we'll do a simple right-to-left replace of the LAST ')' on the line.
            # Assuming the field() call ends on the same line, which they all seem to do.
            if ')' in line:
                # Replace the LAST ')' with ", value=d.get('FieldName', ''))"
                # Wait, if there's a comment at the end of the line, or a comma at the end:
                # field(...),
                
                # Let's split by ')' from the right
                parts = line.rsplit(')', 1)
                if len(parts) == 2:
                    # check if the name is not photo or hdr
                    if name not in ('photo',) and not name.startswith('hdr_'):
                        replacement = f", value=d.get('{name}', ''))"
                        line = parts[0] + replacement + parts[1]

    new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
    
print("Injected values")
