from django.shortcuts import render
from common.views.decorators import login_required


@login_required
def dashboard_view(request):
    """
    Renders the Reports main dashboard.

    Parameters:
        request (HttpRequest): The Django HTTP request object.

    Returns:
        HttpResponse: Rendered reports dashboard template.
    """
    return render(request, 'reports/reports_dashboard.html', {
        'title': 'Reports Dashboard',
        'username': request.session.get('username', 'User'),
        'company_name': request.session.get('company_name', 'Company'),
    })