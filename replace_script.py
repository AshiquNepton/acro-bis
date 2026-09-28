import re

file_path = r'D:\PROJECTS\VsCode Project\ACRO-BIS\common\views\import_excel.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(
    r'    try:\n        with transaction\.atomic\(using=db_alias\):\n            for idx, row in enumerate\(rows\):.*?'
    r'logger\.warning\(\'import row %d error: %s\', excel_row_num, exc\)',
    re.DOTALL
)

replacement = """    try:
        with transaction.atomic(using=db_alias):
            db_rows = []
            
            for idx, row in enumerate(rows):
                excel_row_num = idx + 2
                try:
                    row = {re.sub(r'\\s*\\*\\s*$', '', k).strip(): v for k, v in row.items()}
                    resolved_row = dict(row)
                    for excel_key, category_id in itemgroup_cols.items():
                        raw_val = str(resolved_row.get(excel_key) or '').strip()
                        if not raw_val: continue
                        resolved_row[excel_key] = str(_resolve_itemgroup_id(db_alias, category_id, raw_val, ig_cache))
        
                    db_row = _coerce_row(resolved_row, columns)
                    db_rows.append(db_row)
        
                except Exception as exc:
                    errors.append({'row': excel_row_num, 'error': str(exc)})
                    logger.warning('import row %d error: %s', excel_row_num, exc)
                    
            upsert_batch_fn = config.get('upsert_batch_fn')
            upsert_fn = config.get('upsert_fn')
            
            if upsert_batch_fn and db_rows:
                upsert_batch_fn(db_alias, db_rows)
                imported += len(db_rows)
            else:
                for db_row in db_rows:
                    if upsert_fn:
                        upsert_fn(db_alias, db_row)
                    else:
                        _upsert_row(db_alias, table, pk_col, db_row)
                    imported += 1"""

new_content, count = pattern.subn(replacement, content)
if count > 0:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Success")
else:
    print("Pattern not found")
