# core/generic_views.py
"""
Generic CRUD view factory.

Instead of writing get/save/delete/lookup/search endpoints for every model,
define a registry entry and call make_crud_urls() in your urls.py.
"""

import json as _json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from core.crud import BaseCRUD

logger = logging.getLogger(__name__)

# ─── Global registry ─────────────────────────────────────────────────────────
_REGISTRY: dict = {}


def register(
    key: str,
    table: str,
    pk_col: str,
    field_map: dict,
    db_alias_fn,
    required: list = None,
    table_creator=None,
    search_col: str = None,
    search_display_cols: list = None,
    list_order_by: str = None,
    preserve_empty_on_update: list = None,   # ← NEW
):
    """
    Register a model so generic endpoints can serve it.

    key                      : unique string, e.g. 'hrms:payroll'
    db_alias_fn              : CALLABLE returning the DB alias at request time
    preserve_empty_on_update : form-field names whose empty POST value should
                               NOT overwrite the existing DB value on UPDATE.
                               Typical use: file-path fields like 'photo'.
    """
    _REGISTRY[key] = {
        'table'                   : table,
        'pk_col'                  : pk_col,
        'field_map'               : field_map,
        'db_alias_fn'             : db_alias_fn,
        'required'                : required or [],
        'table_creator'           : table_creator,
        'search_col'              : search_col,
        'search_display_cols'     : search_display_cols,
        'list_order_by'           : list_order_by,
        'preserve_empty_on_update': preserve_empty_on_update or [],   # ← NEW
    }


def _crud(key: str) -> BaseCRUD:
    """Build a BaseCRUD instance from a registry key."""
    cfg = _REGISTRY.get(key)
    if not cfg:
        raise KeyError(f'[generic_views] No registry entry for key "{key}"')
    return BaseCRUD(
        table                    = cfg['table'],
        pk_col                   = cfg['pk_col'],
        field_map                = cfg['field_map'],
        db_alias                 = cfg['db_alias_fn'](),
        required                 = cfg['required'],
        table_creator            = cfg['table_creator'],
        preserve_empty_on_update = cfg['preserve_empty_on_update'],   # ← NEW
    )


# ─── View factories ───────────────────────────────────────────────────────────

def get_view(key: str):
    @require_http_methods(['GET'])
    def _view(request, pk):
        try:
            return _crud(key).get(pk)
        except Exception as e:
            logger.error('[generic get_view] %s: %s', key, e, exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})
    _view.__name__ = f'generic_get_{key}'
    return _view


def save_view(key: str):
    @require_http_methods(['POST'])
    def _view(request):
        try:
            return _crud(key).save(request.POST)
        except Exception as e:
            logger.error('[generic save_view] %s: %s', key, e, exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})
    _view.__name__ = f'generic_save_{key}'
    return _view


def delete_view(key: str):
    @require_http_methods(['POST'])
    def _view(request, pk):
        try:
            return _crud(key).delete(pk)
        except Exception as e:
            logger.error('[generic delete_view] %s: %s', key, e, exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})
    _view.__name__ = f'generic_delete_{key}'
    return _view


def lookup_view(key: str):
    @require_http_methods(['GET'])
    def _view(request):
        field = request.GET.get('field', _REGISTRY[key]['pk_col'])
        value = request.GET.get('value', '').strip()
        if not value:
            return JsonResponse({'success': False, 'error': 'value is required'})
        try:
            return _crud(key).lookup(field, value)
        except Exception as e:
            logger.error('[generic lookup_view] %s: %s', key, e, exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})
    _view.__name__ = f'generic_lookup_{key}'
    return _view


def search_view(key: str):
    @require_http_methods(['GET'])
    def _view(request):
        cfg = _REGISTRY[key]
        search_col = cfg.get('search_col')
        if not search_col:
            return JsonResponse({'success': False, 'error': 'search not configured'})
        q = request.GET.get('q', '').strip()
        if not q:
            return JsonResponse({'success': True, 'results': []})
        try:
            return _crud(key).search(
                q            = q,
                search_col   = search_col,
                display_cols = cfg.get('search_display_cols'),
            )
        except Exception as e:
            logger.error('[generic search_view] %s: %s', key, e, exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})
    _view.__name__ = f'generic_search_{key}'
    return _view


def list_api_view(key: str):
    @require_http_methods(['GET'])
    def _view(request):
        cfg = _REGISTRY[key]
        try:
            return _crud(key).list(order_by=cfg.get('list_order_by'))
        except Exception as e:
            logger.error('[generic list_api_view] %s: %s', key, e, exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})
    _view.__name__ = f'generic_list_{key}'
    return _view