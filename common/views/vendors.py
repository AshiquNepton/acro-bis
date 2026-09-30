import logging
from django.shortcuts import render
from django.http import JsonResponse
from common.views.decorators import login_required
from common.views.party_master import (
    build_party_form_config, save_party, load_party, 
    delete_party, lookup_party, generate_next_party_code, get_party_code_options, base_party_ctx
)

logger = logging.getLogger(__name__)


@login_required
def vendor_form(request):
    ctx = base_party_ctx(request, 'Vendor Management')
    
    # Generate next code or use existing one from request
    ac_code = request.GET.get('AcCode', '').strip()
    next_code = generate_next_party_code(37) if not ac_code else None
    
    # Get options for the dropdown
    ac_code_options = get_party_code_options(37)
    
    ctx['form_config'] = build_party_form_config(
        party_type='vendor',
        ac_code=ac_code or next_code,
        ac_code_options=ac_code_options
    )
    ctx['page_title'] = 'Vendor'
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
