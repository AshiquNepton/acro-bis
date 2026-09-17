"""
errors/handlers.py
==================
Centralized HTTP and JSON Error Handlers for ACRO-BIS Multi-Tenant ERP.

Uniform handling of:
  - 400 Bad Request
  - 403 Forbidden
  - 404 Not Found
  - 500 Internal Server Error

Automatically detects AJAX / fetch requests and returns clean JSON
instead of HTML error pages to avoid breaking frontend UI interactions.
"""

import logging
from django.shortcuts import render
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def _is_ajax(request):
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('Accept', '')
        or request.content_type == 'application/json'
    )


def handler400(request, exception=None):
    logger.warning("400 Bad Request at %s", request.path)
    if _is_ajax(request):
        return JsonResponse({'success': False, 'error': 'Bad Request (400)'}, status=400)
    return render(request, '404.html', {'error_code': '400', 'message': 'Bad Request'}, status=400)


def handler403(request, exception=None):
    logger.warning("403 Forbidden at %s", request.path)
    if _is_ajax(request):
        return JsonResponse({'success': False, 'error': 'Permission Denied (403)'}, status=403)
    return render(request, '404.html', {'error_code': '403', 'message': 'Permission Denied'}, status=403)


def handler404(request, exception=None):
    if _is_ajax(request):
        return JsonResponse({'success': False, 'error': 'Resource Not Found (404)'}, status=404)
    return render(request, '404.html', {'error_code': '404', 'message': 'Page Not Found'}, status=404)


def handler500(request):
    logger.error("500 Internal Server Error at %s", request.path, exc_info=True)
    if _is_ajax(request):
        return JsonResponse({'success': False, 'error': 'Internal Server Error (500). Please check logs.'}, status=500)
    return render(request, '500.html', {'error_code': '500', 'message': 'An unexpected server error occurred'}, status=500)
