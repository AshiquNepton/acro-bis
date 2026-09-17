from django.shortcuts import render, redirect
import logging

logger = logging.getLogger(__name__)


def dashboard_view(request):
    """
    Generic dashboard for unknown business types
    In most cases, users should be redirected to their specific business dashboard
    """
    # Get business type from session
    business_type = request.session.get('business_type', 4)
    
    # Redirect to appropriate dashboard based on business type
    if business_type == 1:  # Laundry
        return redirect('laundry:dashboard')
    elif business_type == 2:  # Restaurant
        return redirect('restaurant:dashboard')
    elif business_type == 4:  # Inventory
        return redirect('inventory:dashboard')
    elif business_type == 5:  # Financial
        return redirect('financial:dashboard')
    
    # Fallback: show generic dashboard
    username = request.session.get('username', 'User')
    company_name = request.session.get('company_name', 'Company')
    
    logger.info(f"Generic dashboard accessed by: {username}")
    
    context = {
        'username': username,
        'company_name': company_name,
        'business_type': 'Unknown',
    }
    
    return render(request, 'common/dashboard/dashboard.html', context)
