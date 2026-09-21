# restaurant/views/dashboard.py

import logging
from django.shortcuts import render
from common.views.decorators import login_required

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    """
    Renders the Restaurant & POS main dashboard.

    Parameters:
        request (HttpRequest): The Django HTTP request object.

    Returns:
        HttpResponse: Rendered restaurant dashboard template.
    """
    username = request.session.get('username', 'User')
    company_name = request.session.get('company_name', 'Company')

    logger.info("Restaurant dashboard accessed by: %s", username)

    context = {
        'username': username,
        'company_name': company_name,
        'business_type': 'Restaurant',
    }

    return render(request, 'restaurant/dashboard/dashboard.html', context)