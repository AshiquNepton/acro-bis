from django.shortcuts import render


def dashboard_view(request):
    """Financial dashboard"""
    return render(request, 'financial/dashboard.html', {
        'title': 'Financial Dashboard',
        'username': request.session.get('username', 'User'),
        'company_name': request.session.get('company_name', 'Company'),
    })
