# inventory/views/dashboard.py

from django.shortcuts import render
from common.views.decorators import login_required


@login_required
def dashboard_view(request):
    """
    Renders the Inventory & Supply Chain main dashboard.

    Parameters:
        request (HttpRequest): The Django HTTP request object.

    Returns:
        HttpResponse: Rendered inventory dashboard template.
    """
    return render(request, 'inventory/dashboard.html', {
        'title': 'Inventory Dashboard',
        'username': request.session.get('username', 'User'),
        'company_name': request.session.get('company_name', 'Company'),
    })                      