# common/middleware/business_guard.py

from django.shortcuts import redirect
from django.urls import resolve
import logging

logger = logging.getLogger(__name__)


class BusinessTypeGuard:
    """
    Middleware to ensure users only access their business type's pages
    
    Prevents:
    - Laundry users from accessing restaurant pages
    - Restaurant users from accessing laundry pages
    
    Allows:
    - Both business types to access common, inventory, financial, reports
    - Unauthenticated access to login/logout pages
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define which apps each business type can access
        self.business_restrictions = {
    1: {  # Laundry
        'allowed': ['laundry', 'common', 'inventory', 'financial', 'reports', 'api'],
        'redirect': 'laundry:dashboard'
    },
    2: {  # Restaurant
        'allowed': ['restaurant', 'common', 'inventory', 'financial', 'reports', 'api'],
        'redirect': 'restaurant:dashboard'
    },
}
        
        # Public paths that don't require authentication or business type check
        self.public_paths = [
            '',
            '/logout/',
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]
    
    def __call__(self, request):
        # Check if path is public
        if any(request.path.startswith(path) for path in self.public_paths):
            return self.get_response(request)
        
        # Check if user is authenticated
        if not request.session.get('is_authenticated'):
            # Not authenticated - redirect handled by AuthenticationMiddleware
            return self.get_response(request)
        
        # Get user's business type
        business_type = request.session.get('business_type')
        
        # If no business type or unknown business type, allow access
        if not business_type or business_type not in self.business_restrictions:
            return self.get_response(request)
        
        # Get current app from URL
        try:
            current_app = resolve(request.path).app_name
        except:
            # If can't resolve, allow access (might be error page, etc.)
            return self.get_response(request)
        
        # If no app name, allow access
        if not current_app:
            return self.get_response(request)
        
        # Get restrictions for this business type
        restrictions = self.business_restrictions[business_type]
        allowed_apps = restrictions['allowed']
        redirect_url = restrictions['redirect']
        
        # Check if user can access this app
        if current_app not in allowed_apps:
            logger.warning(
                f"Business type {business_type} user '{request.session.get('username')}' "
                f"attempted to access '{current_app}' app (not allowed)"
            )
            
            # Redirect to appropriate dashboard
            return redirect(redirect_url)
        
        # Access allowed
        return self.get_response(request)