
import sys
with open('common/views/import_excel.py', 'r') as f:
    text = f.read()
import re
text = re.sub(r'@require_http_methods\(\[''POST''\]\)\s+# -- IMPORT CONFIGURATIONS --', '# -- IMPORT CONFIGURATIONS --', text)
text = text.replace('def import_excel_process(request):', '@require_http_methods([''POST''])\ndef import_excel_process(request):')
with open('common/views/import_excel.py', 'w') as f:
    f.write(text)

