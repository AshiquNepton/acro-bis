# restaurant/views/dashboard.py
# Add this function if it doesn't already exist

from django.shortcuts import render
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)


def dashboard_view(request):
    """
    Restaurant business dashboard
    """
    # Get user info from session
    username = request.session.get('username', 'User')
    company_name = request.session.get('company_name', 'Company')
    
    logger.info(f"Restaurant dashboard accessed by: {username}")
    
    context = {
        'username': username,
        'company_name': company_name,
        'business_type': 'Restaurant',
    }
    
    return render(request, 'restaurant/dashboard.html', context)