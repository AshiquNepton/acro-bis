# core/generic_urls.py
"""
URL pattern factory for generic CRUD endpoints.

Usage in any module's urls.py:

    from core.generic_urls import make_crud_urls

    urlpatterns = [
        # ... your existing patterns ...
    ]

    # Generates 6 URL patterns for payroll:
    urlpatterns += make_crud_urls('hrms:payroll', prefix='payroll')

    # With a string PK (varchar) instead of int:
    urlpatterns += make_crud_urls('hrms:leave', prefix='leave', pk_type='str')

Generated patterns
------------------
    GET  {prefix}/list/           list_api_view   → JSON list
    GET  {prefix}/get/<pk>/       get_view        → single record
    POST {prefix}/save/           save_view       → insert / update
    POST {prefix}/delete/<pk>/    delete_view     → delete
    GET  {prefix}/lookup/         lookup_view     → by any field
    GET  {prefix}/search/         search_view     → ILIKE  (only if search_col set)

URL names
---------
    {module}_{model}_list
    {module}_{model}_get
    {module}_{model}_save
    {module}_{model}_delete
    {module}_{model}_lookup
    {module}_{model}_search

    where key = 'hrms:payroll' → module='hrms', model='payroll'
"""

from django.urls import path
from core.generic_views import (
    get_view, save_view, delete_view,
    lookup_view, search_view, list_api_view,
    _REGISTRY,
)


def make_crud_urls(key: str, prefix: str, pk_type: str = 'str', exclude: list = None) -> list:
    """
    Return a list of url() patterns for the given registry key.

    key      : registry key used in register(), e.g. 'hrms:payroll'
    prefix   : URL prefix WITHOUT leading/trailing slash, e.g. 'payroll'
    pk_type  : 'str' (default, safe for int and varchar PKs) or 'int'
    exclude  : list of endpoint names to skip, e.g. ['save'] when the view
               has a custom save with extra logic (FTP upload etc.)
               Allowed values: 'list', 'get', 'save', 'delete', 'lookup', 'search'
    """
    # Derive clean name prefix from key: 'hrms:payroll' → 'hrms_payroll'
    name_prefix = key.replace(':', '_')
    pk_pattern  = f'<{pk_type}:pk>'

    skip = set(exclude or [])

    patterns = []
    if 'list'   not in skip: patterns.append(path(f'{prefix}/list/',               list_api_view(key), name=f'{name_prefix}_list'))
    if 'get'    not in skip: patterns.append(path(f'{prefix}/get/{pk_pattern}/',   get_view(key),      name=f'{name_prefix}_get'))
    if 'save'   not in skip: patterns.append(path(f'{prefix}/save/',               save_view(key),     name=f'{name_prefix}_save'))
    if 'delete' not in skip: patterns.append(path(f'{prefix}/delete/{pk_pattern}/',delete_view(key),   name=f'{name_prefix}_delete'))
    if 'lookup' not in skip: patterns.append(path(f'{prefix}/lookup/',             lookup_view(key),   name=f'{name_prefix}_lookup'))

    # Only add search URL if the model has search_col configured
    cfg = _REGISTRY.get(key)
    if 'search' not in skip and cfg and cfg.get('search_col'):
        patterns.append(path(f'{prefix}/search/', search_view(key), name=f'{name_prefix}_search'))

    return patterns