# common/middleware/auth.py

import logging
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


class AuthenticationMiddleware:
    """
    Middleware to check if user is authenticated.
    Redirects to login if not authenticated.
    Also stores the next URL for redirect after login.
    Returns JSON 401 Unauthorized for AJAX/fetch requests per docs/SECURITY.md.
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Exact paths that do not require authentication
        self.exact_public_paths = {
            '/',
            '/common/',
            '/common/logout/',
            '/favicon.ico',
        }
        # Path prefixes that do not require authentication
        self.public_prefixes = (
            '/admin/',
            '/static/',
            '/media/',
        )

    def __call__(self, request):
        path = request.path

        # Check if this is a public URL that doesn't require authentication
        is_public = (
            path in self.exact_public_paths
            or any(path.startswith(prefix) for prefix in self.public_prefixes)
        )

        # If not a public URL, check authentication
        if not is_public:
            is_ajax = (
                request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                or 'application/json' in request.headers.get('Accept', '')
                or request.content_type == 'application/json'
            )

            # Check if user is authenticated
            if not request.session.get('is_authenticated'):
                logger.warning("Unauthenticated access attempt to: %s", path)

                if is_ajax:
                    return JsonResponse(
                        {'success': False, 'error': 'Session expired. Please log in again.'},
                        status=401,
                    )

                # Store the URL they were trying to access
                request.session['next_url'] = path
                messages.warning(request, 'Please login to access this page.')
                return redirect('common:login')

            # Check if session has required data
            required_keys = ['username', 'custid', 'db_host', 'db_name', 'db_user', 'db_password']
            missing_keys = [key for key in required_keys if not request.session.get(key)]

            if missing_keys:
                logger.error(
                    "Session missing required keys: %s for user: %s",
                    missing_keys,
                    request.session.get('username'),
                )
                if is_ajax:
                    return JsonResponse(
                        {'success': False, 'error': 'Session incomplete. Please log in again.'},
                        status=401,
                    )

                messages.error(request, 'Your session is incomplete. Please login again.')
                request.session.flush()
                return redirect('common:login')

        response = self.get_response(request)
        return response