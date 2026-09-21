path = 'common/views/party_master.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

history_tabs = '''            {
                'id': 'history', 'label': 'History',
                'columns': [[{'name': 'dummy_hist', 'label': 'History Data', 'type': '5', 'readonly': True, 'rows': 4}]]
            },
            {
                'id': 'transactions', 'label': 'Transactions',
                'columns': [[{'name': 'dummy_trans', 'label': 'Transaction Data', 'type': '5', 'readonly': True, 'rows': 4}]]
            },
            {
                'id': 'alt_address', 'label': 'Alt Address',
'''
code = code.replace("            {\n                'id': 'alt_address', 'label': 'Alt Address',", history_tabs)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print('Added history/trans tabs')
