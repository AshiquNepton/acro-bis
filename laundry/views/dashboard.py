# laundry/views/dashboard.py
# Add this function if it doesn't already exist

from django.shortcuts import render
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)


def dashboard_view(request):
    """
    Laundry business dashboard
    """
    # Get user info from session
    username = request.session.get('username', 'User')
    company_name = request.session.get('company_name', 'Company')
    
    logger.info(f"Laundry dashboard accessed by: {username}")
    
    context = {
        'username': username,
        'company_name': company_name,
        'business_type': 'Laundry',
    }
    
    return render(request, 'laundry/dashboard.html', context)