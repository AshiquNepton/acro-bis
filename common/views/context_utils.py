# common/views/context_utils.py
# ─────────────────────────────────────────────────────────────────────────────
# Determines which module opened a shared common form, so that:
#   1. The correct module sidebar is shown
#   2. Close / Minimize-Close sends user back to the right module dashboard
#
# In any common form view, call:
#   ctx = get_module_context(request)
#   context = { 'form_config': ..., **ctx }
#
# In a sidebar link:
#   <a href="{% url 'common:company_form' %}?next=laundry">Company</a>
# ─────────────────────────────────────────────────────────────────────────────
from django.urls import reverse, NoReverseMatch

# slug → (dashboard url_name, sidebar template path, display label)
MODULE_CONFIG = {
    'common':   ('common:home',        'common/includes/sidebar.html',   'Common'),
    'accounts': ('accounts:dashboard', 'accounts/includes/sidebar.html', 'Accounts'),
    'sales':    ('sales:dashboard',    'sales/includes/sidebar.html',    'Sales'),
    'purchase': ('purchase:dashboard', 'purchase/includes/sidebar.html', 'Purchase'),
    'stock':    ('stock:dashboard',    'stock/includes/sidebar.html',    'Stock'),
}

DEFAULT_MODULE = 'common'


def get_module_context(request):
    """
    Returns dict with:
      back_url          — where Close/Minimize-Close redirects to
      active_module     — slug string e.g. 'laundry'
      sidebar_template  — template path for sidebar include
      module_label      — human readable name
    """
    # 1. Prefer ?next=<module> in the URL
    slug = request.GET.get('next', '').strip().lower()

    # 2. Fall back to session (persists across tab switches within same form)
    if slug not in MODULE_CONFIG:
        slug = request.session.get('active_module', DEFAULT_MODULE)

    if slug not in MODULE_CONFIG:
        slug = DEFAULT_MODULE

    # 3. Save to session
    request.session['active_module'] = slug

    cfg = MODULE_CONFIG[slug]

    # Resolve dashboard URL
    try:
        back_url = reverse(cfg[0])
    except NoReverseMatch:
        back_url = '/'

    # 4. Optional explicit ?back=/laundry/orders/ override
    explicit = request.GET.get('back', '').strip()
    if explicit and explicit.startswith('/'):
        back_url = explicit
        request.session['form_back_url'] = back_url
    elif request.GET.get('next'):
        # Fresh ?next= — reset any stored back url
        request.session.pop('form_back_url', None)

    final_back = request.session.get('form_back_url', back_url)

    return {
        'back_url':         final_back,         # used by __moduleBackUrl in template
        'active_module':    slug,
        'sidebar_template': cfg[1],
        'module_label':     cfg[2],
    }