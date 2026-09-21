import re

path = 'common/views/party_master.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace('db_alias = _get_db(request)\n        with transaction', 'db_alias = _get_db(request)\n        ensure_party_tables(db_alias)\n        with transaction')
code = code.replace("db_alias = _get_db(request)\n    try:\n        with connections", "db_alias = _get_db(request)\n    ensure_party_tables(db_alias)\n    try:\n        with connections")
code = code.replace("db_alias = _get_db(request)\n    try:\n        with transaction", "db_alias = _get_db(request)\n    ensure_party_tables(db_alias)\n    try:\n        with transaction")

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print('Fixed indents properly')
