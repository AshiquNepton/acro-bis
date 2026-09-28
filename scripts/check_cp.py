path = r'D:\PROJECTS\VsCode Project\ACRO-BIS\common\views\context_processors.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_logout = "        {'label': 'Logout',          'url': 'common:logout'},"
new_block  = "        {'label': 'Default Settings', 'url': '#', 'onclick': 'openDefaultSettings()'},\r\n        {'label': 'Logout',          'url': 'common:logout'},"

# Use \r\n aware version
old_logout_rn = "        {'label': 'Logout',          'url': 'common:logout'},"

count_before = content.count(old_logout_rn)
print("Occurrences before:", count_before)

new_content = content.replace(old_logout_rn, new_block)

count_after = new_content.count("Default Settings")
print("Default Settings count after:", count_after)

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Done.")
