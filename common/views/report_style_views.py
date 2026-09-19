# common/views/report_style_views.py
"""
Report Style endpoints — save/load/delete rows in ReportDetails.

All DB access goes through BaseCRUD — no raw SQL in this file.
Table creation / sequence repair is handled by ensure_report_details_table
(common/models/report_details.py), called automatically by BaseCRUD.
"""

import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from common.models.report_details import (
    REPORT_DETAILS_FIELD_MAP,
    ensure_report_details_table,
)
from core.crud import BaseCRUD, safe_atomic

logger = logging.getLogger(__name__)


# ── DB alias helper ───────────────────────────────────────────────────────────

def _get_db_alias(request):
    from common.middleware.database_middleware import get_customer_db
    return (
        request.session.get('db_alias') or
        request.session.get('company_db') or
        get_customer_db()
    )


# ── CRUD factory ──────────────────────────────────────────────────────────────

def _crud(request) -> BaseCRUD:
    """
    Return a BaseCRUD instance for ReportDetails.

    pk_col is 'SlNo' but we never pass SlNo in POST bodies — the serial
    sequence generates it automatically. BaseCRUD's INSERT path only
    includes SlNo in db_data when pk_value is truthy, and since no form
    field maps to SlNo it will never appear in _post_to_db output.
    """
    return BaseCRUD(
        table         = 'ReportDetails',
        pk_col        = 'SlNo',
        field_map     = REPORT_DETAILS_FIELD_MAP,
        db_alias      = _get_db_alias(request),
        table_creator = ensure_report_details_table,
    )


# ── Raw-SQL helpers (only for multi-row bulk ops not in BaseCRUD) ─────────────

def _raw_conn(request):
    from django.db import connections
    return connections[_get_db_alias(request)]


def _style_exists(request, report_name: str, mr_name: str) -> bool:
    with _raw_conn(request).cursor() as cur:
        cur.execute(
            'SELECT COUNT(*) FROM "ReportDetails" WHERE "ReportName"=%s AND "MRName"=%s',
            [report_name, mr_name],
        )
        return cur.fetchone()[0] > 0


def _delete_style_rows(request, report_name: str, mr_name: str) -> int:
    with _raw_conn(request).cursor() as cur:
        cur.execute(
            'DELETE FROM "ReportDetails" WHERE "ReportName"=%s AND "MRName"=%s',
            [report_name, mr_name],
        )
        return cur.rowcount


# ══════════════════════════════════════════════════════════════════════════════
#  POST /common/report/save-style/
# ══════════════════════════════════════════════════════════════════════════════

@require_http_methods(['POST'])
def report_save_style(request):
    """
    Save (or overwrite) a named report style.

    Body (JSON):
        report_name : str   — style name chosen by user
        mr_name     : str   — master report name  e.g. 'EmployeeReport'
        details     : list  — array of column dicts (one per ReportDetails row)
        overwrite   : bool  — if true, delete existing rows first

    Flow:
        1. Ensure table exists (via ensure_report_details_table).
        2. If overwrite=false AND rows already exist → return exists:true.
        3. If overwrite=true  → DELETE existing rows.
        4. INSERT each detail row via BaseCRUD.save() — SlNo is auto-generated
           by the sequence; it is never included in the POST data.
    """
    if not request.session.get('is_authenticated'):
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)

    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    report_name = str(body.get('report_name', '') or '').strip()
    mr_name     = str(body.get('mr_name',     '') or '').strip()
    details     = body.get('details', []) or []
    overwrite   = bool(body.get('overwrite', False))

    if not report_name:
        return JsonResponse({'success': False, 'error': 'report_name is required'})
    if not mr_name:
        return JsonResponse({'success': False, 'error': 'mr_name is required'})
    if not details:
        return JsonResponse({'success': False, 'error': 'details array is empty'})

    try:
        ensure_report_details_table(_get_db_alias(request))

        exists = _style_exists(request, report_name, mr_name)

        if exists and not overwrite:
            return JsonResponse({
                'success': False,
                'exists' : True,
                'message': f'Style "{report_name}" already exists.',
            })

        cols = [
            'ReportName', 'MRName', 'Section', 'FName', 'UFName',
            'Width', 'Index', 'Alignment', 'Show', 'Heder', 'Break',
            'UIndex', 'UWidth', 'MReport', 'DField', 'Font', 'FieldType',
            'FormatText', 'FontName', 'SYS_ITEM', 'Color', 'TextColor',
            'FKTable', 'FKIDField', 'FKField'
        ]
        col_clause = ', '.join(f'"{c}"' for c in cols)
        val_placeholder = ', '.join(['%s'] * len(cols))

        def _int(val, default=0):
            try:
                return int(val) if val not in (None, '', 'None') else default
            except (ValueError, TypeError):
                return default

        def _flt(val, default=0.0):
            try:
                return float(val) if val not in (None, '', 'None') else default
            except (ValueError, TypeError):
                return default

        rows_to_insert = []
        for d in details:
            rows_to_insert.append([
                report_name,
                mr_name,
                str(d.get('Section',    '') or '')[:50],
                str(d.get('FName',      '') or '')[:150],
                str(d.get('UFName',     '') or '')[:50],
                _flt(d.get('Width')),
                _flt(d.get('Index')),
                _flt(d.get('Alignment')),
                _int(d.get('Show'),      1),
                _int(d.get('Heder'),     0),
                _int(d.get('Break'),     0),
                _flt(d.get('UIndex')),
                _flt(d.get('UWidth')),
                _int(d.get('MReport'),   0),
                _int(d.get('DField'),    0),
                _int(d.get('Font'),      0),
                _int(d.get('FieldType'), 1),
                str(d.get('FormatText',  '') or '')[:50],
                str(d.get('FontName',    '') or '')[:45],
                _int(d.get('SYS_ITEM'),  0),
                str(d.get('Color',       '') or '')[:20],
                str(d.get('TextColor',   '') or '')[:20],
                str(d.get('FKTable',     '') or '')[:100],
                str(d.get('FKIDField',   '') or '')[:100],
                str(d.get('FKField',     '') or '')[:100],
            ])

        db_alias = _get_db_alias(request)
        with safe_atomic(db_alias):
            with _raw_conn(request).cursor() as cur:
                if exists:
                    cur.execute(
                        'DELETE FROM "ReportDetails" WHERE "ReportName"=%s AND "MRName"=%s',
                        [report_name, mr_name]
                    )
                for row_vals in rows_to_insert:
                    cur.execute(
                        f'INSERT INTO "ReportDetails" ({col_clause}) VALUES ({val_placeholder})',
                        row_vals
                    )

        return JsonResponse({
            'success': True,
            'message': f'Style "{report_name}" saved ({len(details)} columns).',
        })

    except Exception as exc:
        logger.error('[report_save_style] %s', exc, exc_info=True)
        return JsonResponse({'success': False, 'error': str(exc)}, status=500)


# ══════════════════════════════════════════════════════════════════════════════
#  GET /common/report/load-style/
# ══════════════════════════════════════════════════════════════════════════════

@require_http_methods(['GET'])
def report_load_style(request):
    """
    Load column definitions for a saved report style.

    Query params:  report_name, mr_name

    Response:
        { "success": true, "cols": [ {key, label, show, ...}, ... ] }

    Columns are ordered by "Index" ascending.
    Raw SQL is used here because BaseCRUD.list() doesn't support a clean
    multi-column WHERE + ORDER BY in one call. The table is still guaranteed
    to exist via ensure_report_details_table.
    """
    if not request.session.get('is_authenticated'):
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)

    report_name = request.GET.get('report_name', '').strip()
    mr_name     = request.GET.get('mr_name',     '').strip()

    if not report_name or not mr_name:
        return JsonResponse({'success': False, 'error': 'report_name and mr_name are required'})

    try:
        ensure_report_details_table(_get_db_alias(request))

        with _raw_conn(request).cursor() as cur:
            cur.execute("""
                SELECT "Section", "FName", "Show", "Width", "Index",
                       "Alignment", "FieldType", "FormatText",
                       COALESCE("Color",     '') AS "Color",
                       COALESCE("TextColor", '') AS "TextColor",
                       COALESCE("FKTable",   '') AS "FKTable",
                       COALESCE("FKIDField", '') AS "FKIDField",
                       COALESCE("FKField",   '') AS "FKField"
                FROM   "ReportDetails"
                WHERE  "ReportName" = %s
                  AND  "MRName"     = %s
                ORDER  BY "Index" ASC
            """, [report_name, mr_name])
            rows = cur.fetchall()

        if not rows:
            return JsonResponse({
                'success': False,
                'error'  : f'Style "{report_name}" not found in {mr_name}',
            })

        cols = []
        for i, row in enumerate(rows):
            section, fname, show, width, index, align, ftype, fmt, color, text_color, fk_table, fk_id_field, fk_field = row
            cols.append({
                'key'      : str(section  or '').strip(),
                'label'    : str(fname    or '').strip(),
                'show'     : bool(int(show or 1)),
                'total'    : False,
                'wrap'     : False,
                'format'   : str(fmt      or '').strip(),
                'col'      : int(index    or i + 1),
                'fieldType': int(ftype    or 1),
                'width'    : float(width  or 0),
                'align'    : int(align    or 0),
                'color'    : str(color     or '').strip(),
                'textColor': str(text_color or '').strip(),
                'fkTable'  : str(fk_table    or '').strip(),
                'fkIdField': str(fk_id_field or '').strip(),
                'fkField'  : str(fk_field    or '').strip(),
            })

        return JsonResponse({'success': True, 'cols': cols})

    except Exception as exc:
        logger.error('[report_load_style] %s', exc, exc_info=True)
        return JsonResponse({'success': False, 'error': str(exc)}, status=500)


# ══════════════════════════════════════════════════════════════════════════════
#  POST /common/report/delete-style/
# ══════════════════════════════════════════════════════════════════════════════

@require_http_methods(['POST'])
def report_delete_style(request):
    """
    Delete all rows for a named style.

    Body (JSON):  { report_name, mr_name }
    """
    if not request.session.get('is_authenticated'):
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)

    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    report_name = str(body.get('report_name', '') or '').strip()
    mr_name     = str(body.get('mr_name',     '') or '').strip()

    if not report_name or not mr_name:
        return JsonResponse({'success': False, 'error': 'report_name and mr_name are required'})

    try:
        ensure_report_details_table(_get_db_alias(request))
        deleted = _delete_style_rows(request, report_name, mr_name)

        return JsonResponse({
            'success': True,
            'message': f'Deleted style "{report_name}" ({deleted} rows).',
        })

    except Exception as exc:
        logger.error('[report_delete_style] %s', exc, exc_info=True)
        return JsonResponse({'success': False, 'error': str(exc)}, status=500)
    
    