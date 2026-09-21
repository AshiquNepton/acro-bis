path = 'common/views/import_excel.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if "header_fill    = PatternFill('solid', start_color='2563EB', end_color='2563EB')  # blue" in line:
        continue
    if "req_fill       = PatternFill('solid', start_color='1D4ED8', end_color='1D4ED8')  # darker blue for required" in line:
        continue
    if "header_font    = Font(name='Arial', bold=True, color='FFFFFF', size=10)" in line:
        new_lines.append('''    theme = request.session.get('theme', 'red-white')
    if theme == 'purple-white':
        bg, bg_req = '7C3AED', '6D28D9'
    elif theme == 'blue-white':
        bg, bg_req = '2563EB', '1D4ED8'
    elif theme == 'green-white':
        bg, bg_req = '16A34A', '15803D'
    elif theme == 'teal-white':
        bg, bg_req = '0F766E', '0D6B63'
    else:
        bg, bg_req = 'C0123C', '960E2F'

    header_font    = Font(name='Arial', bold=True, color='FFFFFF', size=10)
    header_fill    = PatternFill('solid', start_color=bg, end_color=bg)
    req_fill       = PatternFill('solid', start_color=bg_req, end_color=bg_req)
''')
    else:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Updated colors')
