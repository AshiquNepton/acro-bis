# common/views/context_processors.py

def company_context(request):
    """
    Makes company_info available in every template automatically.
    Add to settings.py → TEMPLATES → OPTIONS → context_processors.
    """
    return {
        'company_info': {
            'id':        request.session.get('company_id'),
            'name':      request.session.get('company_name', ''),
            'arabic':    request.session.get('company_arabic', ''),
            'subtitle':  request.session.get('company_subtitle', ''),
            'period_from': request.session.get('period_from', ''),
            'period_to':   request.session.get('period_to', ''),
            'business_type': request.session.get('business_type'),
            'tin':       request.session.get('company_tin', ''),
            'cr':        request.session.get('company_cr', ''),
        }
    }


import json
from common.views.global_settings import _build_gs_config

def global_settings_config(request):
    """Injects gs_config_json so base.html can render window._gsConfig."""
    try:
        return {'gs_config_json': json.dumps(_build_gs_config())}
    except Exception:
        return {'gs_config_json': '{}'}

def sidebar_context(request):
    """
    Provides navbar_config and layout_base to all templates based on software_id.
    """
    from common.theme_constants import TOOLBAR_ICONS as I
    software_id = request.session.get('software_id')
    
    layout_base = 'common/layout.html'
    
    if software_id == 1:
        layout_base = 'laundry/base.html'
        navbar_config = {
            'sections': [
                {
                    'id': 'orders', 'label': 'Orders', 'icon': I['Note'], 'active': True,
                    'items': [
                        {'label': 'New Order',        'url': 'laundry:new_order'},
                        {'label': 'Pending Orders',   'url': 'laundry:pending_orders', 'count': 5},
                        {'label': 'Completed Orders', 'url': 'laundry:completed_orders'},
                    ]
                },
                {
                    'id': 'customers', 'label': 'Customers', 'icon': I['Customer'],
                    'items': [
                        {'label': 'All Customers', 'url': 'laundry:customers'},
                        {'label': 'Add Customer',  'url': 'laundry:add_customer'},
                    ]
                },
                {
                    'id': 'services', 'label': 'Services', 'icon': I['Tools'],
                    'items': [
                        {'label': 'Service List', 'url': 'laundry:services'},
                        {'label': 'Pricing',      'url': 'laundry:pricing'},
                    ]
                },
                {
                    'id': 'settings', 'label': 'Settings', 'icon': I['Settings'],
                    'items': [
                        {'label': 'Company Info',    'url': 'common:company_form'},
                        {'label': 'Database Config', 'url': 'common:database_config'},
                        {'label': 'Theme',           'url': 'common:theme_settings'},
                        {'label': 'Logout',          'url': 'common:logout'},
                    ]
                },
            ]
        }
    elif software_id == 2:
        layout_base = 'restaurant/base.html'
        navbar_config = {
            'sections': [
                {
                    'id': 'orders', 'label': 'Orders', 'icon': I['Invoice'], 'active': True,
                    'items': [
                        {'label': 'New Order',        'url': 'restaurant:new_order'},
                        {'label': 'Pending Orders',   'url': 'restaurant:pending_orders', 'count': 3},
                        {'label': 'Completed Orders', 'url': 'restaurant:completed_orders'},
                    ]
                },
                {
                    'id': 'menu', 'label': 'Menu', 'icon': I['Menu'],
                    'items': [
                        {'label': 'All Items',  'url': 'restaurant:menu_items'},
                        {'label': 'Add Item',   'url': 'restaurant:add_item'},
                        {'label': 'Categories', 'url': 'restaurant:categories'},
                    ]
                },
                {
                    'id': 'tables', 'label': 'Tables', 'icon': I['Dashboard'],
                    'items': [
                        {'label': 'All Tables',   'url': 'restaurant:tables'},
                        {'label': 'Reservations', 'url': 'restaurant:reservations'},
                    ]
                },
                {
                    'id': 'settings', 'label': 'Settings', 'icon': I['Settings'],
                    'items': [
                        {'label': 'Company Info',    'url': 'common:company_form'},
                        {'label': 'Database Config', 'url': 'common:database_config'},
                        {'label': 'Theme',           'url': 'common:theme_settings'},
                        {'label': 'Logout',          'url': 'common:logout'},
                    ]
                },
            ]
        }
    elif software_id == 4:  # Inventory
        layout_base = 'inventory/base.html'
        navbar_config = {
            'sections': [
                {
                    'id': 'dashboard', 'label': 'Dashboard', 'icon': I['Dashboard'], 'active': True,
                    'items': [
                        {'label': 'Overview', 'url': 'inventory:dashboard'},
                    ]
                },
                {
                    'id': 'inventory', 'label': 'Inventory', 'icon': I['Note'],
                    'items': [
                        {'label': 'Item Master', 'url': 'inventory:item_master'},
                        {'label': 'Stock Entry', 'url': '#'},
                        {'label': 'Purchase Order', 'url': '#'},
                    ]
                },
                {
                    'id': 'masters', 'label': 'Masters', 'icon': I['Customer'],
                    'items': [
                        {'label': 'Company Info', 'url': 'common:company_form'},
                        {'label': 'Customers',    'url': 'common:customer'},
                        {'label': 'Group Setup',  'url': 'common:group_setup'},
                        {'label': 'Employee / Dept', 'url': 'common:department_form'},
                        {'label': 'Import from Excel', 'url': 'common:import_excel_view'},
                    ]
                },
                {
                    'id': 'reports', 'label': 'Reports', 'icon': I['Note'],
                    'items': [
                        {'label': 'Stock Report', 'url': 'reports:stock_report'},
                    ]
                },
                {
                    'id': 'settings', 'label': 'Settings', 'icon': I['Settings'],
                    'items': [
                        {'label': 'Database Config', 'url': 'common:database_config'},
                        {'label': 'Theme',           'url': 'common:theme_settings'},
                        {'label': 'Logout',          'url': 'common:logout'},
                    ]
                },
            ]
        }
    elif software_id == 5:  # Financial
        layout_base = 'financial/base.html'
        navbar_config = {
            'sections': [
                {
                    'id': 'dashboard', 'label': 'Dashboard', 'icon': I['Dashboard'], 'active': True,
                    'items': [
                        {'label': 'Overview', 'url': 'financial:dashboard'},
                    ]
                },
                {
                    'id': 'accounts', 'label': 'Accounts', 'icon': I['Note'],
                    'items': [
                        {'label': 'Chart of Accounts', 'url': '#'},
                        {'label': 'Journal Voucher', 'url': '#'},
                        {'label': 'Payment Voucher', 'url': '#'},
                        {'label': 'Receipt Voucher', 'url': '#'},
                    ]
                },
                {
                    'id': 'masters', 'label': 'Masters', 'icon': I['Customer'],
                    'items': [
                        {'label': 'Company Info', 'url': 'common:company_form'},
                        {'label': 'Customers',    'url': 'common:customer'},
                        {'label': 'Group Setup',  'url': 'common:group_setup'},
                        {'label': 'Employee / Dept', 'url': 'common:department_form'},
                        {'label': 'Import from Excel', 'url': 'common:import_excel_view'},
                    ]
                },
                {
                    'id': 'settings', 'label': 'Settings', 'icon': I['Settings'],
                    'items': [
                        {'label': 'Database Config', 'url': 'common:database_config'},
                        {'label': 'Theme',           'url': 'common:theme_settings'},
                        {'label': 'Logout',          'url': 'common:logout'},
                    ]
                },
            ]
        }
    else:
        navbar_config = {
            'sections': [
                {
                    'id': 'masters', 'label': 'Masters', 'icon': I['Dashboard'], 'active': True,
                    'items': [
                        {'label': 'Company Info', 'url': 'common:company_form'},
                        {'label': 'Customers',    'url': 'common:customer'},
                        {'label': 'Group Setup',  'url': 'common:group_setup'},
                        {'label': 'Employee / Dept', 'url': 'common:department_form'},
                        {'label': 'Import from Excel', 'url': 'common:import_excel_view'},
                    ]
                },
                {
                    'id': 'settings', 'label': 'Settings', 'icon': I['Settings'],
                    'items': [
                        {'label': 'Database Config', 'url': 'common:database_config'},
                        {'label': 'Theme',           'url': 'common:theme_settings'},
                        {'label': 'Logout',          'url': 'common:logout'},
                    ]
                },
            ]
        }
        
    return {
        'navbar_config': navbar_config,
        'layout_base': layout_base
    }