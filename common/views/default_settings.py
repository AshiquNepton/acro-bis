# common/views/default_settings.py
"""
Default Settings — load/save for the Default Settings modal
============================================================
Persists everything in ChartOfCode.

Rate Captions (aligned with existing get_rate_captions() reader):
    Category='Captions'   Code='RATE0'…'RATE5'   TypeCode='value'
    → existing item_master.get_rate_captions() reads:
        WHERE Category LIKE 'Captions%' AND Code LIKE 'RATE%'

Group Captions:
    Category='Captions'   Code='GROUP1'…'GROUP5'  TypeCode='value'

Other Captions (warehouses, company, category, brand, city, area, district, state):
    Category='Captions'   Code='<UPPER_KEY>'      TypeCode='value'

Inventory Settings:
    Category='DefaultSettings'  Code='settings'   TypeCode=<field_name>
"""

import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from common.middleware.database_middleware import get_customer_db
from common.models.chart_of_code import ChartOfCode
from common.views.decorators import login_required

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# ChartOfCode categories
# ─────────────────────────────────────────────────────────────────────────────
DS_CATEGORY     = 'DefaultSettings'
DS_SETT_CODE    = 'settings'
CAP_CATEGORY    = 'Captions'        # aligned with get_rate_captions()

# ─────────────────────────────────────────────────────────────────────────────
# Known inventory-settings fields and their defaults
# ─────────────────────────────────────────────────────────────────────────────
SETT_FIELDS = {
    'inv_item_multiunit_visibility': 'true',
    'inv_item_group_visibility':     'true',
}

# ─────────────────────────────────────────────────────────────────────────────
# Caption fields — (ChartOfCode Code, default label)
# Rates: aligned with existing get_rate_captions() that reads Code LIKE 'RATE%'
# Groups: ItemGroup1..5 shown in item form
# Others: used across forms
# ─────────────────────────────────────────────────────────────────────────────
CAPTION_FIELDS = {
    # Rates (Rate0–Rate5) — 6 levels
    'RATE0':      'Purchase Price',
    'RATE1':      'MRP',
    'RATE2':      'DRP',
    'RATE3':      'FDP',
    'RATE4':      'Rate 4',
    'RATE5':      'Rate 5',
    # Item Groups (ItemGroup1–ItemGroup5) — 5 groups
    'GROUP1':     'Group 1',
    'GROUP2':     'Group 2',
    'GROUP3':     'Group 3',
    'GROUP4':     'Group 4',
    'GROUP5':     'Group 5',
    # Other field captions
    'WAREHOUSES': 'Warehouse',
    'COMPANY':    'Company',
    'CATEGORY':   'Category',
    'BRAND':      'Brand',
    'CITY':       'City',
    'AREA':       'Area',
    'DISTRICT':   'District',
    'STATE':      'State',
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _coc_get_sett(db, type_code):
    return ChartOfCode.get(db, category=DS_CATEGORY, code=DS_SETT_CODE, type_code=type_code)


def _coc_set_sett(db, type_code, value):
    ChartOfCode.set(
        db,
        category    = DS_CATEGORY,
        code        = DS_SETT_CODE,
        type_code   = type_code,
        description = str(value),
    )


def _coc_get_cap(db, code):
    return ChartOfCode.get(db, category=CAP_CATEGORY, code=code, type_code='value')


def _coc_set_cap(db, code, value):
    ChartOfCode.set(
        db,
        category    = CAP_CATEGORY,
        code        = code,
        type_code   = 'value',
        description = str(value),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Inventory Settings endpoints
# ─────────────────────────────────────────────────────────────────────────────

@require_http_methods(['GET'])
@login_required
def ds_load(request):
    """Return all default-settings values (falls back to defaults if not yet saved)."""
    db = get_customer_db()
    result = {}
    for field, default in SETT_FIELDS.items():
        stored = _coc_get_sett(db, field)
        result[field] = stored if stored is not None else default
    return JsonResponse({'success': True, 'settings': result})


@require_http_methods(['POST'])
@login_required
def ds_save(request):
    """Save default-settings values posted as JSON body."""
    try:
        data = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    db    = get_customer_db()
    saved = []
    for field in SETT_FIELDS:
        if field in data:
            try:
                _coc_set_sett(db, field, data[field])
                saved.append(field)
            except Exception as e:
                logger.error('[ds_save] field=%s error=%s', field, e, exc_info=True)

    return JsonResponse({'success': True, 'saved': saved})


# ─────────────────────────────────────────────────────────────────────────────
# Captions endpoints
# ─────────────────────────────────────────────────────────────────────────────

@require_http_methods(['GET'])
@login_required
def ds_load_captions(request):
    """
    Return all captions.
    Reads from ChartOfCode(Category='Captions', Code=<UPPER_KEY>)
    Falls back to default labels when not yet saved.
    """
    db = get_customer_db()
    result = {}
    for code, default in CAPTION_FIELDS.items():
        stored = _coc_get_cap(db, code)
        result[code] = stored if stored is not None else default
    return JsonResponse({'success': True, 'captions': result})


@require_http_methods(['POST'])
@login_required
def ds_save_captions(request):
    """
    Save captions.
    Expects JSON body: { "captions": { "RATE0": "Purchase Price", ... } }
    Stores to ChartOfCode(Category='Captions', Code=<key>) so that
    existing get_rate_captions() in item_master.py picks them up automatically.
    """
    try:
        data     = json.loads(request.body)
        captions = data.get('captions', {})
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    db    = get_customer_db()
    saved = []
    for code in CAPTION_FIELDS:
        if code in captions:
            try:
                _coc_set_cap(db, code, captions[code])
                saved.append(code)
            except Exception as e:
                logger.error('[ds_save_captions] code=%s error=%s', code, e, exc_info=True)

    return JsonResponse({'success': True, 'saved': saved})
