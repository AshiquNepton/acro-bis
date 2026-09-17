# common/middleware/auth.py

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)


class AuthenticationMiddleware:
    """
    Middleware to check if user is authenticated
    Redirects to login if not authenticated
    Also stores the next URL for redirect after login
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs that don't require authentication (public URLs)
        self.public_paths = [
            '',
            '/admin/',
            '/static/',
            '/media/',
        ]
    
    def __call__(self, request):
        # Get the current path
        path = request.path
        
        # Check if this is a public URL that doesn't require authentication
        is_public = False
        for public_path in self.public_paths:
            if path.startswith(public_path):
                is_public = True
                break
        
        # If not a public URL, check authentication
        if not is_public:
            # Check if user is authenticated
            if not request.session.get('is_authenticated'):
                logger.warning(f"Unauthenticated access attempt to: {path}")
                
                # Store the URL they were trying to access
                request.session['next_url'] = path
                
                # Add a message
                messages.warning(request, 'Please login to access this page.')
                
                # Redirect to login
                return redirect('common:login')
            
            # Check if session has required data
            required_keys = ['username', 'custid', 'db_host', 'db_name', 'db_user', 'db_password']
            missing_keys = [key for key in required_keys if not request.session.get(key)]
            
            if missing_keys:
                logger.error(f"Session missing required keys: {missing_keys} for user: {request.session.get('username')}")
                messages.error(request, 'Your session is incomplete. Please login again.')
                request.session.flush()
                return redirect('common:login')
        
        response = self.get_response(request)
        return response