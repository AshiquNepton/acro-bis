import logging
from django.shortcuts import render
from django.http import JsonResponse
from common.views.decorators import login_required
from common.views.party_master import build_party_form_config, save_party, load_party, delete_party, lookup_party

logger = logging.getLogger(__name__)

def _base_ctx(request, title):
    return {
        'page_title': title,
        'user_info': {'name': request.session.get('username', 'User'), 'id': request.session.get('custid', 'N/A')},
    }

@login_required
def customer_form(request):
    ctx = _base_ctx(request, 'Customer Management')
    ctx['form_config'] = build_party_form_config('customer')
    return render(request, 'common/masters/customer_form.html', ctx)

def save_customer(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    return save_party(request, 36)

def load_customer(request):
    return load_party(request, 36)

def delete_customer(request):
    return delete_party(request, 36)

def lookup_customer(request):
    return lookup_party(request, 36)
