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
def vendor_form(request):
    ctx = _base_ctx(request, 'Vendor Management')
    ctx['form_config'] = build_party_form_config('vendor')
    return render(request, 'common/masters/vendor_form.html', ctx)

def save_vendor(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    return save_party(request, 37)

def load_vendor(request):
    return load_party(request, 37)

def delete_vendor(request):
    return delete_party(request, 37)

def lookup_vendor(request):
    return lookup_party(request, 37)
