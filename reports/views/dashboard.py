from django.shortcuts import render


def dashboard_view(request):
    """Reports dashboard"""
    return render(request, 'reports/reports_dashboard.html', {
        'title': 'Reports Dashboard',
        'username': request.session.get('username', 'User'),
        'company_name': request.session.get('company_name', 'Company'),
    })