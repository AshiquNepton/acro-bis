from common.views.import_excel import register_import_type
from common.views.party_master import ensure_party_tables
from django.db import connections, transaction
import logging

logger = logging.getLogger(__name__)

PARTY_COLS = [
    {'excel': 'AcCode',      'db_col': 'AcCode',      'type': 'str', 'required': True},
    {'excel': 'Name',        'db_col': 'Description', 'type': 'str', 'required': True},
    {'excel': 'Arabic Name', 'db_col': 'ArabicDesc',  'type': 'str'},
    {'excel': 'Address 1',   'db_col': 'Address1',    'type': 'str'},
    {'excel': 'Address 2',   'db_col': 'Address2',    'type': 'str'},
    {'excel': 'Address 3',   'db_col': 'Address3',    'type': 'str'},
    {'excel': 'PinCode',     'db_col': 'PinCode',     'type': 'str'},
    {'excel': 'City',        'db_col': 'City',        'type': 'str'},
    {'excel': 'Phone',       'db_col': 'Phone',       'type': 'str'},
    {'excel': 'Mobile',      'db_col': 'Mobile',      'type': 'str'},
    {'excel': 'Email',       'db_col': 'Email',       'type': 'str'},
    {'excel': 'Fax',         'db_col': 'Fax',         'type': 'str'},
    {'excel': 'Contact',     'db_col': 'Contact',     'type': 'str'},
    {'excel': 'VAT Number',  'db_col': 'VATNumber',   'type': 'str'},
    {'excel': 'TIN No',      'db_col': 'TINNO',       'type': 'str'},
    {'excel': 'CST No',      'db_col': 'CST',         'type': 'str'},
    {'excel': 'Credit Limit','db_col': 'CreditLimit', 'type': 'float'},
    {'excel': 'Credit Days', 'db_col': 'CreditDys',   'type': 'float'},
    {'excel': 'Discount %',  'db_col': 'Discount',    'type': 'float'},
    {'excel': 'Remarks',     'db_col': 'Remarks',     'type': 'str'},
]

def make_upsert_fn(mgroup):
    def upsert_fn(db_alias, db_row):
        ensure_party_tables(db_alias)
        ac_code = db_row.get('AcCode')
        description = db_row.get('Description')
        if not ac_code or not description:
            raise ValueError('AcCode and Name are required')
            
        with transaction.atomic(using=db_alias):
            with connections[db_alias].cursor() as cur:
                # Check if exists
                cur.execute('SELECT "AccountID" FROM "ChartOfAccounts" WHERE "AcCode" = %s AND "MGroup" = %s', [ac_code, mgroup])
                row = cur.fetchone()
                
                if row:
                    account_id = row[0]
                    cur.execute('''
                        UPDATE "ChartOfAccounts"
                        SET "Description"=%s, "ArabicDesc"=%s, "Address1"=%s
                        WHERE "AccountID"=%s
                    ''', [description, db_row.get('ArabicDesc'), db_row.get('Address1'), account_id])
                    
                    cv_fields = ['Address2', 'Address3', 'PinCode', 'City', 'Phone', 'Mobile', 'Email', 'Fax', 
                                 'Contact', 'VATNumber', 'TINNO', 'CST', 'CreditLimit', 'CreditDys', 'Discount', 'Remarks']
                    set_clause = ", ".join([f'"{f}" = %s' for f in cv_fields])
                    params = [db_row.get(f) for f in cv_fields] + [account_id]
                    cur.execute(f'UPDATE "CustomerVendor" SET {set_clause} WHERE "AccountID" = %s', params)
                else:
                    cur.execute('SELECT MAX("AccountID") FROM "ChartOfAccounts"')
                    max_id = cur.fetchone()[0] or 0
                    account_id = max_id + 1
                    
                    cur.execute('''
                        INSERT INTO "ChartOfAccounts" 
                        ("AccountID", "MGroup", "AcCode", "Description", "ArabicDesc", "GroupID", "Active", "Address1")
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ''', [account_id, mgroup, ac_code, description, db_row.get('ArabicDesc'), 1, 1, db_row.get('Address1')])
                    
                    cv_fields = ['Address2', 'Address3', 'PinCode', 'City', 'Phone', 'Mobile', 'Email', 'Fax', 
                                 'Contact', 'VATNumber', 'TINNO', 'CST', 'CreditLimit', 'CreditDys', 'Discount', 'Remarks']
                    cols = '"AccountID", ' + ", ".join([f'"{f}"' for f in cv_fields])
                    vals = "%s, " + ", ".join(["%s"] * len(cv_fields))
                    params = [account_id] + [db_row.get(f) for f in cv_fields]
                    cur.execute(f'INSERT INTO "CustomerVendor" ({cols}) VALUES ({vals})', params)
    return upsert_fn

def register_party_imports():
    register_import_type('customer', {
        'label': 'Customer Master',
        'table': 'CustomerVendor',
        'pk_col': 'AcCode',
        'db_alias_fn': lambda: 'customer_db',
        'columns': PARTY_COLS,
        'upsert_fn': make_upsert_fn(36)
    })
    
    register_import_type('vendor', {
        'label': 'Vendor Master',
        'table': 'CustomerVendor',
        'pk_col': 'AcCode',
        'db_alias_fn': lambda: 'customer_db',
        'columns': PARTY_COLS,
        'upsert_fn': make_upsert_fn(37)
    })
