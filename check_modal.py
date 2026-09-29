import re

file_path = r'D:\PROJECTS\VsCode Project\ACRO-BIS\inventory\templates\inventory\items\item_master_form.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'function initSelectItemModal\(\) \{.*?\n\}', content, flags=re.DOTALL)
if match:
    print(match.group(0))
