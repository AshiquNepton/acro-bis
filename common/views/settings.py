# common/views/settings.py
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from core.dbhelper import DatabaseHelper
from datetime import datetime, timedelta
from common.theme_constants import VALID_THEMES, DEFAULT_THEME, TOOLBAR_ICONS


# ─── Shared context ───────────────────────────────────────────────────────────

def get_common_context():
    return {
        'company_info': {
            'name': 'Nepton Business System',
            'short_name': 'Nepton',
            'tagline': 'Business System',
            'expiry_date': (datetime.now() + timedelta(days=365)).strftime('%d %b %Y'),
        },
        'user_info': {
            'name': 'Muhammed Ashiqu',
            'id': 'ASHIQU',
            'account': 'AQWE#'
        },
        'navbar_config': {'sections': []}
    }



# ─── Home ─────────────────────────────────────────────────────────────────────

def home(request):
    if not request.session.get('is_authenticated'):
        return redirect('common:login')

    user_info = {
        'name':        request.session.get('username', 'User'),
        'id':          request.session.get('custid', 'N/A'),
        'software_id': request.session.get('software_id'),
        'customer_id': request.session.get('customer_id'),
    }

    company_name   = request.session.get('company_name', 'Your Company')
    company_expiry = request.session.get('company_expiry', 'N/A')

    if company_expiry and company_expiry != 'N/A':
        try:
            formatted_expiry = company_expiry if isinstance(company_expiry, str) else company_expiry.strftime('%d %b %Y')
        except Exception:
            formatted_expiry = str(company_expiry)
    else:
        formatted_expiry = '31 Dec 2025'

    company_info = {
        'name':        request.session.get('company_name', 'Your Company'),
        'short_name':  request.session.get('company_name', 'Company')[:10],
        'tagline':     request.session.get('company_subtitle', 'Business System'),
        'expiry_date': request.session.get('period_to', 'N/A'),
    }

    context = {
        'page_title':    'Dashboard',
        'user_info':     user_info,
        'company_info':  company_info,
        'show_form':     False,
    }

    return render(request, 'common/home.html', context)


# ─── Database Config ──────────────────────────────────────────────────────────

def database_config(request):
    db_configured = DatabaseHelper.is_configured()
    db_config = {'HOST': '', 'PORT': '5432', 'NAME': '', 'USER': '', 'PASSWORD': ''}

    if db_configured:
        loaded_config = DatabaseHelper.load_credentials()
        if loaded_config:
            db_config.update(loaded_config)
            db_config['PASSWORD'] = '********'

    db_form_config = {
        'form_id': 'database-config-form',
        'hero': {
            'show_avatar': False,
            'hero_icon': TOOLBAR_ICONS['Settings'],
            'default_name': 'PostgreSQL Database Connection',
            'show_meta_rows': False,
        },
        'toolbar': [
            {'label': 'Close',           'icon': TOOLBAR_ICONS['Close'],    'onclick': "window.location.href='{% url \"common:home\" %}'"},
            {'label': 'Test Connection', 'icon': TOOLBAR_ICONS['Utilities'], 'onclick': 'testConnection()'},
            {'label': 'Save',            'icon': TOOLBAR_ICONS['Save'],     'onclick': 'saveDatabase()'},
        ],
        'header_fields': [],
        'show_sidenav': False,
        'tabs': [
            {
                'id': 'main', 'label': 'Connection',
                'columns': [
                    [
                        {'name': 'db_host',     'label': 'Database Host', 'type': 'text',     'required': True,  'placeholder': 'e.g., localhost or 192.168.1.100', 'value': db_config.get('HOST', '')},
                        {'name': 'db_name',     'label': 'Database Name', 'type': 'text',     'required': True,  'placeholder': 'Enter database name',              'value': db_config.get('NAME', '')},
                        {'name': 'db_user',     'label': 'Username',      'type': 'text',     'required': True,  'placeholder': 'postgres',                         'value': db_config.get('USER', '')},
                    ],
                    [
                        {'name': 'db_port',     'label': 'Port',          'type': 'number',   'required': True,  'placeholder': '5432',          'value': db_config.get('PORT', '5432')},
                        {'name': 'db_password', 'label': 'Password',      'type': 'password', 'required': True,  'placeholder': 'Enter password'},
                    ],
                ]
            }
        ]
    }

    context = {
        'db_form_config': db_form_config,
        'db_configured':  db_configured,
        'page_title':     'Database Configuration',
    }

    return render(request, 'common/settings/database_config.html', context)


def save_database_config(request):
    if request.method == 'POST':
        db_config = {
            'engine':   'postgresql',
            'name':     request.POST.get('db_name'),
            'user':     request.POST.get('db_user'),
            'password': request.POST.get('db_password'),
            'host':     request.POST.get('db_host'),
            'port':     request.POST.get('db_port'),
        }
        success, message = DatabaseHelper.test_connection(db_config)
        if success:
            DatabaseHelper.save_credentials(db_config)
            messages.success(request, 'Database configuration saved! Please restart the server.')
            return redirect('common:home')
        else:
            messages.error(request, f'Connection failed: {message}')
            return redirect('common:database_config')
    return redirect('common:home')


def test_database_connection(request):
    if request.method == 'POST':
        db_config = {
            'engine':   'postgresql',
            'name':     request.POST.get('db_name'),
            'user':     request.POST.get('db_user'),
            'password': request.POST.get('db_password'),
            'host':     request.POST.get('db_host'),
            'port':     request.POST.get('db_port'),
        }
        success, message = DatabaseHelper.test_connection(db_config)
        return JsonResponse({
            'success': success,
            'message': message if success else None,
            'error':   message if not success else None,
        })
    return JsonResponse({'success': False, 'error': 'Invalid request'})


# ─── Theme Settings ───────────────────────────────────────────────────────────

def theme_settings(request):
    if not request.session.get('is_authenticated'):
        return redirect('common:login')
    ctx = {
        'page_title': 'Theme Settings',
        'user_info': {
            'name': request.session.get('username', 'User'),
            'id':   request.session.get('custid', 'N/A'),
        },
    }
    return render(request, 'common/settings/theme_settings.html', ctx)


def save_theme(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    try:
        data  = json.loads(request.body)
        theme = data.get('theme', '').strip()
    except (ValueError, KeyError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    if theme not in VALID_THEMES:
        return JsonResponse({'success': False, 'error': 'Unknown theme'}, status=400)

    request.session['theme']  = theme
    request.session.modified  = True
    return JsonResponse({'success': True, 'theme': theme})