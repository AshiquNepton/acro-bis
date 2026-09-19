# common/views/customers.py
import json
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import connections
from common.views.decorators import login_required
from core.crud import BaseCRUD
from common.theme_constants import tb

logger = logging.getLogger(__name__)

def _db(request):
    return 'customer_db'

def _base_ctx(request, title):
    company_name   = request.session.get('company_name', 'Your Company')
    company_expiry = request.session.get('company_expiry', 'N/A')
    try:
        formatted_expiry = (company_expiry if isinstance(company_expiry, str)
                            else company_expiry.strftime('%d %b %Y'))
    except Exception:
        formatted_expiry = str(company_expiry)

    return {
        'page_title':   title,
        'company_info': {
            'name':        company_name,
            'short_name':  company_name[:10] if company_name else 'Company',
            'tagline':     'Business System',
            'expiry_date': formatted_expiry,
        },
        'user_info': {
            'name': request.session.get('username', 'User'),
            'id':   request.session.get('custid',   'N/A'),
        },
        'navbar_config': {'sections': []},
    }

CUSTOMER_FIELD_MAPPING = {
    'CustomerCode':       'customer_code',
    'FirstName':          'first_name',
    'LastName':           'last_name',
    'CompanyName':        'company_name',
    'CustomerType':       'customer_type',
    'Email':              'email',
    'Phone':              'phone',
    'Mobile':             'mobile',
    'ShipAddress1':       'ship_address1',
    'ShipAddress2':       'ship_address2',
    'ShipCity':           'ship_city',
    'ShipState':          'ship_state',
    'ShipZip':            'ship_zip',
    'ShipCountry':        'ship_country',
    'BillAddress1':       'bill_address1',
    'BillAddress2':       'bill_address2',
    'BillCity':           'bill_city',
    'BillState':          'bill_state',
    'BillZip':            'bill_zip',
    'BillCountry':        'bill_country',
    'PreferredLanguage':  'preferred_language',
    'CreditLimit':        'credit_limit',
    'PaymentTerms':       'payment_terms',
    'TaxNo':              'tax_no',
    'Notes':              'notes',
}

def _crud(request):
    return BaseCRUD(
        table='Customers',
        pk_col='CustomerCode',
        field_map=CUSTOMER_FIELD_MAPPING,
        db_alias=_db(request),
        required=['customer_code', 'first_name']
    )

def _build_form_config():
    CUSTOMER_TYPE_OPTIONS = [
        {'value': '',           'label': 'Select...'},
        {'value': 'individual', 'label': 'Individual'},
        {'value': 'business',   'label': 'Business'},
        {'value': 'vip',        'label': 'VIP'},
    ]
    LANGUAGE_OPTIONS = [
        {'value': '',   'label': 'Select...'},
        {'value': 'en', 'label': 'English'},
        {'value': 'ar', 'label': 'Arabic'},
    ]
    PAYMENT_OPTIONS = [
        {'value': '',        'label': 'Select...'},
        {'value': 'cash',    'label': 'Cash'},
        {'value': 'credit',  'label': 'Credit'},
        {'value': 'net30',   'label': 'Net 30'},
        {'value': 'net60',   'label': 'Net 60'},
    ]

    return {
        'form_id': 'customer-form',
        'title':   'Customer Information',
        'toolbar': [
            tb('Close',  'cuClose()',  danger=True),
            tb('Save',   'cuSave()'),
            tb('New',    'cuNew()'),
            tb('Delete', 'cuDelete()'),
        ],
        'menu_items': [
            tb('Menu',   'cfMenu(this)', sep_after=True),
            tb('Print',  'window.print()'),
        ],
        'header_fields': [
            {
                'name': 'customer_code', 'label': 'Customer Code',
                'type': '1', 'required': True, 'width': '160px', 'lookup_btn': True,
            },
            {
                'name': 'first_name', 'label': 'First Name',
                'type': '1', 'required': True, 'width': '200px',
            },
            {
                'name': 'last_name', 'label': 'Last Name',
                'type': '1', 'required': True, 'width': '200px',
            },
            {
                'name': 'customer_type', 'label': 'Type',
                'type': '3', 'required': True, 'width': '160px',
                'options': CUSTOMER_TYPE_OPTIONS,
            },
        ],
        'tabs': [
            {
                'id': 'general', 'label': '» General',
                'columns': [
                    [
                        {'name': 'company_name',    'label': 'Company Name',  'type': '1'},
                        {'name': 'email',           'label': 'Email',         'type': '13', 'required': True},
                        {'name': 'phone',           'label': 'Phone',         'type': '14', 'required': True},
                        {'name': 'mobile',          'label': 'Mobile',        'type': '14'},
                        {'name': 'tax_no',          'label': 'Tax No',        'type': '1'},
                        {'name': 'credit_limit',    'label': 'Credit Limit',  'type': '2'},
                        {'name': 'payment_terms',   'label': 'Payment Terms', 'type': '3', 'options': PAYMENT_OPTIONS},
                        {'name': 'preferred_language', 'label': 'Language',   'type': '3', 'options': LANGUAGE_OPTIONS},
                    ],
                    [
                        {'name': 'notes', 'label': 'Notes', 'type': '5', 'rows': 5},
                    ],
                ],
            },
            {
                'id': 'shipping', 'label': '» Shipping',
                'columns': [
                    [
                        {'name': 'ship_address1', 'label': 'Address 1', 'type': '1'},
                        {'name': 'ship_address2', 'label': 'Address 2', 'type': '1'},
                        {'name': 'ship_city',     'label': 'City',      'type': '1'},
                        {'name': 'ship_state',    'label': 'State',     'type': '1'},
                    ],
                    [
                        {'name': 'ship_zip',     'label': 'ZIP Code', 'type': '1'},
                        {'name': 'ship_country', 'label': 'Country',  'type': '1'},
                    ],
                ],
            },
            {
                'id': 'billing', 'label': '» Billing',
                'columns': [
                    [
                        {'name': 'bill_address1', 'label': 'Address 1', 'type': '1'},
                        {'name': 'bill_address2', 'label': 'Address 2', 'type': '1'},
                        {'name': 'bill_city',     'label': 'City',      'type': '1'},
                        {'name': 'bill_state',    'label': 'State',     'type': '1'},
                    ],
                    [
                        {'name': 'bill_zip',     'label': 'ZIP Code', 'type': '1'},
                        {'name': 'bill_country', 'label': 'Country',  'type': '1'},
                    ],
                ],
            },
        ],
    }

@login_required
def customer_form(request):
    ctx = _base_ctx(request, 'Customer Management')
    ctx['form_config'] = _build_form_config()
    return render(request, 'common/masters/customer_form.html', ctx)

def save_customer(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    return _crud(request).save(request.POST)

def lookup_customer(request):
    field = request.GET.get('field', 'CustomerCode')
    value = request.GET.get('value', '').strip()
    return _crud(request).lookup(field, value)

def delete_customer(request, pk_value):
    return _crud(request).delete(pk_value)
