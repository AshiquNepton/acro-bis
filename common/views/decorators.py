# common/views/decorators.py
"""
Security decorators for ACRO-BIS ERP.

All view functions MUST be decorated with @login_required.
Do NOT use Django's built-in login_required — this project uses
a custom session-based auth system (common.middleware.auth).

Usage
─────
    from common.views.decorators import login_required

    @login_required
    def my_view(request):
        ...
"""
import functools
import logging

from django.http import JsonResponse
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


def login_required(view_func):
    """
    Decorator that enforces session-based authentication.

    - Redirects unauthenticated GET requests to the login page.
    - Returns JSON { success: false, error: 'Unauthenticated' } for
      POST / AJAX requests so the frontend can handle it gracefully.
    - Preserves the original function name, docstring, and module
      (via functools.wraps) so introspection and Django's URL resolver work.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_authenticated'):
            logger.warning(
                'Unauthenticated access: %s %s',
                request.method, request.path,
            )
            # AJAX / JSON requests — return JSON error instead of redirect
            is_ajax = (
                request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                or 'application/json' in request.headers.get('Accept', '')
            )
            if is_ajax or request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
                return JsonResponse(
                    {'success': False, 'error': 'Session expired. Please log in again.'},
                    status=401,
                )
            # Standard page request — redirect to login
            return redirect('common:login')
        return view_func(request, *args, **kwargs)

    return wrapper


def require_session_keys(*keys):
    """
    Decorator that verifies required session keys exist.
    Use after @login_required when a view needs specific session data.

    Usage
    ─────
        @login_required
        @require_session_keys('custid', 'db_host')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            missing = [k for k in keys if not request.session.get(k)]
            if missing:
                logger.error(
                    'Session missing required keys %s for user %s',
                    missing, request.session.get('username'),
                )
                return JsonResponse(
                    {'success': False, 'error': 'Session incomplete. Please log in again.'},
                    status=401,
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator