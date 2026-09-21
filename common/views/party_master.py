"""
common/views/party_master.py

View-layer helpers for the Customer / Vendor (Party) feature.

Responsibilities
────────────────
  - build_party_form_config()  — constructs the profile-form UI configuration
                                 dict used by both the customer and vendor forms
  - Thin re-exports of service functions so existing callers of
    common.views.party_master.save_party / load_party / delete_party / lookup_party
    continue to work without import changes

All DB operations are delegated to common.services.party_service.
Table schema definitions live in common.models.customer and common.models.supplier.
"""

from common.theme_constants import tb

# ── Re-export service functions (backward-compatible) ────────────────────────
from common.services.party_service import (   # noqa: F401
    save_party,
    load_party,
    delete_party,
    lookup_party,
    ensure_party_tables,
    generate_next_party_code,
    get_party_code_options,
)


# ── UI configuration ─────────────────────────────────────────────────────────

def build_party_form_config(party_type: str, ac_code: str = None, ac_code_options: list = None) -> dict:
    """
    Return the profile-form configuration dict for a customer or vendor form.

    party_type: 'customer' | 'vendor'
    """
    is_cust = (party_type == 'customer')
    title = 'Customer Master' if is_cust else 'Vendor Master'
    
    ac_code_options = ac_code_options or []
    if ac_code and not any(opt.get('value') == ac_code for opt in ac_code_options):
        ac_code_options.append({'value': ac_code, 'label': f"{ac_code} (New)"})

    return {
        'form_id': f'{party_type}-form',
        'title': title,
        'hero': {
            'show_avatar': True,
            'default_name': 'New Account',
            'badge1_label': 'Status',
            'badge1_field': 'Status',
        },
        'toolbar': [
            tb('Close',  'pfClose()',  danger=True),
            tb('Save',   'pfSave()'),
            tb('New',    'pfNew()'),
            tb('Delete', 'pfDelete()'),
        ],
        'menu_items': [
            tb('Menu',  'pfMenu(this)', sep_after=True),
            tb('Print', 'window.print()'),
        ],
        'header_fields': [
            {
                'name': 'AcCode', 
                'label': f'{title.split()[0]} Code',
                'type': '19', 
                'required': True, 
                'width': '160px', 
                'lookup_btn': True,
                'value': ac_code,
                'options': ac_code_options,
                'onchange': 'pfLookupNow(this.form.id)'
            },
            {
                'name': 'Description', 'label': f'{title.split()[0]} Name',
                'type': '1', 'required': True, 'width': '350px',
            },
            {
                'name': 'ArabicDesc', 'label': 'Arabic Name',
                'type': '1', 'width': '250px',
            },
            {
                'name': 'GroupID', 'label': 'Group',
                'type': '2', 'width': '100px', 'required': True, 'default': '1',
            },
            {
                'name': 'Active', 'label': 'Active',
                'type': '10', 'default': True,
            },
        ],
        'tabs': [
            {
                'id': 'general', 'label': 'General Info',
                'columns': [
                    [
                        {'name': 'Address1', 'label': 'Address 1',    'type': '1'},
                        {'name': 'Address2', 'label': 'Address 2',    'type': '1'},
                        {'name': 'Address3', 'label': 'Address 3',    'type': '1'},
                        {'name': 'PinCode',  'label': 'Pin/Zip Code', 'type': '1'},
                        {'name': 'City',     'label': 'City',         'type': '1'},
                    ],
                    [
                        {'name': 'Phone',   'label': 'Phone',          'type': '14'},
                        {'name': 'Mobile',  'label': 'Mobile',         'type': '14'},
                        {'name': 'Email',   'label': 'Email',          'type': '13'},
                        {'name': 'Fax',     'label': 'Fax',            'type': '1'},
                        {'name': 'Contact', 'label': 'Contact Person', 'type': '1'},
                    ],
                ],
            },
            {
                'id': 'tax_financial', 'label': 'Tax & Financial',
                'columns': [
                    [
                        {'name': 'VATNumber',   'label': 'VAT Number',   'type': '1'},
                        {'name': 'TINNO',       'label': 'TIN No',       'type': '1'},
                        {'name': 'CST',         'label': 'CST No',       'type': '1'},
                        {'name': 'CreditLimit', 'label': 'Credit Limit', 'type': '2'},
                        {'name': 'CreditDys',   'label': 'Credit Days',  'type': '2'},
                    ],
                    [
                        {'name': 'PricingLevel', 'label': 'Pricing Level', 'type': '2'},
                        {'name': 'Discount',     'label': 'Discount %',    'type': '2'},
                        {'name': 'Remarks',      'label': 'Remarks',       'type': '5', 'rows': 4},
                    ],
                ],
            },
            {
                'id': 'contacts', 'label': 'Contacts',
                'columns': [
                    [
                        {'name': 'ContName1',  'label': 'Contact 1 Name',   'type': '1'},
                        {'name': 'ContMob1',   'label': 'Contact 1 Mobile', 'type': '14'},
                        {'name': 'ContEmail1', 'label': 'Contact 1 Email',  'type': '1'},
                    ],
                    [
                        {'name': 'ContName2',  'label': 'Contact 2 Name',   'type': '1'},
                        {'name': 'ContMob2',   'label': 'Contact 2 Mobile', 'type': '14'},
                        {'name': 'ContEmail2', 'label': 'Contact 2 Email',  'type': '1'},
                    ],
                ],
            },
            {
                'id': 'history', 'label': 'History',
                'columns': [[
                    {'name': 'dummy_hist', 'label': 'History Data', 'type': '5', 'readonly': True, 'rows': 4},
                ]],
            },
            {
                'id': 'transactions', 'label': 'Transactions',
                'columns': [[
                    {'name': 'dummy_trans', 'label': 'Transaction Data', 'type': '5', 'readonly': True, 'rows': 4},
                ]],
            },
            {
                'id': 'alt_address', 'label': 'Alt Address',
                'columns': [
                    [
                        {'name': 'AltAddress1', 'label': 'Alt Address 1', 'type': '1'},
                        {'name': 'AltAddress2', 'label': 'Alt Address 2', 'type': '1'},
                        {'name': 'AltPinCode',  'label': 'Alt Pin Code',  'type': '1'},
                    ],
                    [
                        {'name': 'AltContact', 'label': 'Alt Contact', 'type': '1'},
                        {'name': 'AltPhone',   'label': 'Alt Phone',   'type': '14'},
                        {'name': 'AltMobile',  'label': 'Alt Mobile',  'type': '14'},
                    ],
                ],
            },
        ],
    }
