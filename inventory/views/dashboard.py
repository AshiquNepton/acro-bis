# inventory/views.py

from django.shortcuts import render


def dashboard_view(request):
    """Inventory dashboard"""
    return render(request, 'inventory/dashboard.html', {
        'title': 'Inventory Dashboard',
        'username': request.session.get('username', 'User'),
        'company_name': request.session.get('company_name', 'Company'),
    })                      