# common/views/filter_views.py
"""
Filter CRUD endpoints — shared across all modules.

FilterDetails table:
    ReportName  varchar(20)  — matches r.id from report config (e.g. 'emp-report')
    FieldName   varchar(20)  — actual data field key (e.g. 'emp_name')
    DisplayName varchar(20)  — label shown to user
    FieldType   smallint     — 1=text, 2=number, 3=select/foreign, 6=date, 7=time
    FilterSql   varchar(150) — SQL fragment for foreign/select type
    ColWidth    varchar(15)  — column width hint (e.g. "3500,1500")
    IDField     varchar(20)  — ID field name for foreign type
    Default     smallint     — 1=default filter row shown on open
    Operator    int          — 0=AND, 1=OR
"""

import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from common.middleware.database_middleware import get_customer_db
from common.models.company_information import ensure_organization_logo_columns
from common.models.filter_details import ensure_filter_details_table
import re

logger = logging.getLogger(__name__)


# ── DB helpers ────────────────────────────────────────────────────────────────

def _get_conn():
    from django.db import connections
    alias = get_customer_db()
    return connections[alias]


def _ensure_filter_table():
    alias = get_customer_db()
    ensure_filter_details_table(db_alias=alias)


# ── List distinct report names ────────────────────────────────────────────────

@require_http_methods(['GET'])
def filter_reports(request):
    """
    GET /common/filter/reports/
    Returns all distinct ReportNames in FilterDetails, sorted.
    Used to populate the ReportName dropdown in the Edit Filter modal.
    """
    try:
        _ensure_filter_table()
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT "ReportName"
                FROM   "FilterDetails"
                WHERE  "ReportName" IS NOT NULL
                  AND  "ReportName" <> ''
                ORDER  BY "ReportName"
            """)
            names = [row[0] for row in cur.fetchall()]
        return JsonResponse({'success': True, 'reports': names})
    except Exception as e:
        logger.error('[filter_reports] %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


# ── Load filter definitions for a report ──────────────────────────────────────

@require_http_methods(['GET'])
def filter_load(request):
    """
    GET /common/filter/load/?report=emp-report
    Returns all FilterDetails rows for the given report name.
    """
    report_name = request.GET.get('report', '').strip()
    if not report_name:
        return JsonResponse({'success': False, 'error': 'report param required'})

    try:
        _ensure_filter_table()
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "FieldName", "DisplayName", "FieldType", "FilterSql",
                       "ColWidth", "IDField", "Default", "Operator"
                FROM   "FilterDetails"
                WHERE  "ReportName" = %s
                ORDER  BY "Default" DESC, "FieldName"
                """,
                [report_name],
            )
            cols = [c[0] for c in cur.description]
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]

        for r in rows:
            for k, v in r.items():
                if v is None:
                    r[k] = ''

        return JsonResponse({'success': True, 'filters': rows})

    except Exception as e:
        logger.error('[filter_load] %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


# ── Save (upsert) a single filter definition ──────────────────────────────────

@require_http_methods(['POST'])
def filter_save(request):
    """
    POST /common/filter/save/
    Body: report_name, field_name, display_name, field_type,
          filter_sql, col_width, id_field, is_default, operator
    """
    try:
        if request.content_type and 'application/json' in request.content_type:
            body = json.loads(request.body)
        else:
            body = request.POST

        report_name  = str(body.get('report_name',  '') or '').strip()[:20]
        field_name   = str(body.get('field_name',   '') or '').strip()[:20]
        display_name = str(body.get('display_name', '') or '').strip()[:20]
        field_type   = int(body.get('field_type',   1)  or 1)
        filter_sql   = str(body.get('filter_sql',   '') or '').strip()[:150]
        col_width    = str(body.get('col_width',    '') or '').strip()[:15]
        id_field     = str(body.get('id_field',     '') or '').strip()[:20]
        is_default   = int(body.get('is_default',   0)  or 0)
        operator     = int(body.get('operator',     0)  or 0)

        if not report_name or not field_name:
            return JsonResponse({'success': False, 'error': 'report_name and field_name are required'})

        _ensure_filter_table()
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO "FilterDetails"
                    ("ReportName", "FieldName", "DisplayName", "FieldType",
                     "FilterSql", "ColWidth", "IDField", "Default", "Operator")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT ("ReportName", "FieldName") DO UPDATE SET
                    "DisplayName" = EXCLUDED."DisplayName",
                    "FieldType"   = EXCLUDED."FieldType",
                    "FilterSql"   = EXCLUDED."FilterSql",
                    "ColWidth"    = EXCLUDED."ColWidth",
                    "IDField"     = EXCLUDED."IDField",
                    "Default"     = EXCLUDED."Default",
                    "Operator"    = EXCLUDED."Operator"
                """,
                [report_name, field_name, display_name, field_type,
                 filter_sql, col_width, id_field, is_default, operator],
            )

        return JsonResponse({'success': True, 'message': 'Saved'})

    except Exception as e:
        logger.error('[filter_save] %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


# ── Delete a single filter definition ─────────────────────────────────────────

@require_http_methods(['POST'])
def filter_delete(request):
    """
    POST /common/filter/delete/
    Body: report_name, field_name
    """
    try:
        if request.content_type and 'application/json' in request.content_type:
            body = json.loads(request.body)
        else:
            body = request.POST

        report_name = str(body.get('report_name', '') or '').strip()
        field_name  = str(body.get('field_name',  '') or '').strip()

        if not report_name or not field_name:
            return JsonResponse({'success': False, 'error': 'report_name and field_name required'})

        _ensure_filter_table()
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                'DELETE FROM "FilterDetails" WHERE "ReportName" = %s AND "FieldName" = %s',
                [report_name, field_name],
            )

        return JsonResponse({'success': True, 'message': 'Deleted'})

    except Exception as e:
        logger.error('[filter_delete] %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


# ── Reset (delete all definitions for a report) ───────────────────────────────

@require_http_methods(['POST'])
def filter_reset(request):
    """
    POST /common/filter/reset/
    Body: report_name
    Deletes ALL FilterDetails rows for the report.
    """
    try:
        if request.content_type and 'application/json' in request.content_type:
            body = json.loads(request.body)
        else:
            body = request.POST

        report_name = str(body.get('report_name', '') or '').strip()
        if not report_name:
            return JsonResponse({'success': False, 'error': 'report_name required'})

        _ensure_filter_table()
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute('DELETE FROM "FilterDetails" WHERE "ReportName" = %s', [report_name])

        return JsonResponse({'success': True, 'message': 'Reset'})

    except Exception as e:
        logger.error('[filter_reset] %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


# ── Rename a report ───────────────────────────────────────────────────────────

@require_http_methods(['POST'])
def filter_rename(request):
    """
    POST /common/filter/rename/
    Body: old_name, new_name
    Updates ReportName on ALL rows matching old_name.
    Rejects if new_name already exists (would cause PK conflict).
    """
    try:
        if request.content_type and 'application/json' in request.content_type:
            body = json.loads(request.body)
        else:
            body = request.POST

        old_name = str(body.get('old_name', '') or '').strip()[:20]
        new_name = str(body.get('new_name', '') or '').strip()[:20]

        if not old_name or not new_name:
            return JsonResponse({'success': False, 'error': 'old_name and new_name are required'})

        if old_name == new_name:
            return JsonResponse({'success': False, 'error': 'New name is the same as the current name'})

        _ensure_filter_table()
        conn = _get_conn()
        with conn.cursor() as cur:
            # Prevent merging into an existing report
            cur.execute(
                'SELECT COUNT(*) FROM "FilterDetails" WHERE "ReportName" = %s',
                [new_name],
            )
            if cur.fetchone()[0] > 0:
                return JsonResponse({
                    'success': False,
                    'error'  : f'"{new_name}" already exists. Delete it first or choose a different name.',
                })

            cur.execute(
                'UPDATE "FilterDetails" SET "ReportName" = %s WHERE "ReportName" = %s',
                [new_name, old_name],
            )
            updated = cur.rowcount

        return JsonResponse({
            'success' : True,
            'message' : f'Renamed "{old_name}" → "{new_name}" ({updated} row(s))',
            'new_name': new_name,
        })

    except Exception as e:
        logger.error('[filter_rename] %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})
    

def _get_company_db_from_request(request):
    """
    Return the company-specific DB alias from the session.
    Mirrors the pattern in common/views/department.py → _get_company_db(request).
    Adjust the session key names to match what your middleware stores.
    """
    from common.middleware.database_middleware import get_customer_db
    # Try the keys your project actually uses; fall back to get_customer_db()
    return (
        request.session.get('db_alias') or
        request.session.get('company_db') or
        get_customer_db()
    )
 
 
@require_http_methods(['GET'])
def filter_report_styles(request):
    """
    GET /common/filter/report-styles/?mr_name=EmployeeReport
 
    Returns distinct ReportName values from ReportDetails
    where MRName = mr_name.  Populates the Report Style <select>
    in the filter modal.
 
    Response shape:
        { "success": true, "styles": ["Style A", "Style B"] }
    """
    from django.db import connections
 
    mr_name = request.GET.get('mr_name', '').strip()
    if not mr_name:
        return JsonResponse({'success': True, 'styles': []})
 
    try:
        db_alias = _get_company_db_from_request(request)
        with connections[db_alias].cursor() as cur:
            cur.execute(
                'SELECT DISTINCT "ReportName" '
                'FROM "ReportDetails" '
                'WHERE "MRName" = %s '
                '  AND "ReportName" IS NOT NULL '
                'ORDER BY "ReportName"',
                [mr_name]
            )
            styles = [row[0] for row in cur.fetchall()]
        return JsonResponse({'success': True, 'styles': styles})
 
    except Exception as exc:
        logger.error('filter_report_styles: %s', exc, exc_info=True)
        return JsonResponse({'success': False, 'error': str(exc), 'styles': []})
 
 
@require_http_methods(['GET'])
def filter_dept_options(request):
    """
    Returns FirmID as value and FName as label so the dept filter
    can match the integer Department column in Employees.
    """
    try:
        from common.models.firm_master import FirmMaster, ensure_firm_master_table

        db_alias = _get_company_db_from_request(request)
        ensure_firm_master_table(db_alias)

        firms = (
            FirmMaster.objects
            .using(db_alias)
            .filter(FStatus=1)
            .exclude(FName__isnull=True)
            .exclude(FName='')
            .values('FirmID', 'FName')
            .order_by('FName')
        )
        options = [{'value': str(f['FirmID']), 'label': f['FName']} for f in firms]
        return JsonResponse({'success': True, 'options': options})

    except Exception as exc:
        logger.error('filter_dept_options: %s', exc, exc_info=True)
        return JsonResponse({'success': False, 'error': str(exc), 'options': []})
    
 
@require_http_methods(['GET'])
def filter_period_dates(request):
    """
    GET /common/filter/period-dates/
 
    Returns PeriodFrom and PeriodTo from the Organization table.
    Used to auto-fill Date From / Date To in the filter modal with
    the current company's financial year.
 
    Response shape:
        { "success": true, "period_from": "2024-01-01", "period_to": "2024-12-31" }
    """
    try:
        from common.middleware.database_middleware import get_customer_db
        from common.models.company_information import Organization
 
        customer_db = get_customer_db()
        ensure_organization_logo_columns(customer_db)   # ← add this line
        org = Organization.objects.using(customer_db).first()
        if not org:
            return JsonResponse({
                'success': False,
                'error': 'No organization found',
                'period_from': '',
                'period_to': '',
            })
 
        period_from = org.PeriodFrom.strftime('%Y-%m-%d') if org.PeriodFrom else ''
        period_to   = org.PeriodTo.strftime('%Y-%m-%d')   if org.PeriodTo   else ''
        return JsonResponse({
            'success'    : True,
            'period_from': period_from,
            'period_to'  : period_to,
        })
 
    except Exception as exc:
        logger.error('filter_period_dates: %s', exc, exc_info=True)
        return JsonResponse({
            'success'    : False,
            'error'      : str(exc),
            'period_from': '',
            'period_to'  : '',
        })
 

@require_http_methods(['POST'])
def filter_log(request):
    """
    POST /common/filter/log/
    Body: { "message": "..." }
    Prints the filter summary to the VS Code / Django terminal.
    Returns 204 — no content needed by the client.
    """
    try:
        body = json.loads(request.body)
        msg  = str(body.get('message', '')).strip()
        if msg:
            print(msg)
            logger.info('[filter_log] %s', msg)
    except Exception:
        pass
    from django.http import HttpResponse
    return HttpResponse(status=204)


@require_http_methods(['GET'])
def filter_foreign_options(request):
    """
    GET /common/filter/foreign-options/?report=emp-report&field=nationality

    Reads FilterSql + IDField for a FieldType=3 row and executes the query
    to return {value, label} pairs for the autocomplete dropdown.

    FilterSql stored example : "Description From ItemGroups Where Category=51 and"
    IDField stored example   : "GroupID"

    Built query:
        SELECT "GroupID", "Description" FROM "ItemGroups" WHERE "Category" = 51
    """
    report_name = request.GET.get('report', '').strip()
    field_name  = request.GET.get('field',  '').strip()
    if not report_name or not field_name:
        return JsonResponse({'success': True, 'options': []})

    try:
        _ensure_filter_table()
        conn = _get_conn()

        with conn.cursor() as cur:
            cur.execute(
                'SELECT "FilterSql", "IDField", "FieldType" '
                'FROM "FilterDetails" '
                'WHERE "ReportName" = %s AND "FieldName" = %s',
                [report_name, field_name],
            )
            row = cur.fetchone()

        if not row:
            return JsonResponse({'success': True, 'options': []})

        filter_sql = (row[0] or '').strip()
        id_field   = (row[1] or '').strip()
        field_type = int(row[2] or 1)

        if field_type != 3 or not filter_sql or not id_field:
            return JsonResponse({'success': True, 'options': []})

        full_sql = _build_foreign_sql(filter_sql, id_field)
        if not full_sql:
            logger.warning('filter_foreign_options: could not parse FilterSql=%r', filter_sql)
            return JsonResponse({'success': True, 'options': []})

        with conn.cursor() as cur:
            cur.execute(full_sql)
            options = [
                {'value': str(r[0]), 'label': str(r[1])}
                for r in cur.fetchall()
                if r[1] is not None and str(r[1]).strip()
            ]

        return JsonResponse({'success': True, 'options': options})

    except Exception as exc:
        logger.error('filter_foreign_options: %s', exc, exc_info=True)
        return JsonResponse({'success': False, 'error': str(exc), 'options': []})


def _build_foreign_sql(filter_sql: str, id_field: str) -> str:
    """
    Converts a loose FilterSql fragment into a safe, fully-quoted PostgreSQL SELECT.

    Handles the format stored by the Edit Filter modal:
        "<LabelCol> From <Table> Where <Col>=<val> [AND|OR]"

    Examples
    --------
    filter_sql = "Description From ItemGroups Where Category=51 and"
    id_field   = "GroupID"
    →  SELECT "GroupID","Description" FROM "ItemGroups" WHERE "Category"=51 ORDER BY 2

    filter_sql = "FName From FirmMaster Where FStatus=1"
    id_field   = "FirmID"
    →  SELECT "FirmID","FName" FROM "FirmMaster" WHERE "FirmID" IS NOT NULL AND "FStatus"=1 ORDER BY 2
    """
    import re

    # Strip trailing AND / OR / whitespace that the Edit Filter modal appends
    cleaned = re.sub(r'\s+(AND|OR)\s*$', '', filter_sql, flags=re.IGNORECASE).strip()

    # Parse:  <label_col> From <table> [Where <conditions>]
    m = re.match(
        r'^(\w+)\s+From\s+(\w+)(?:\s+Where\s+(.+))?$',
        cleaned,
        flags=re.IGNORECASE,
    )
    if not m:
        return ''

    label_col  = m.group(1)          # e.g. Description
    table_name = m.group(2)          # e.g. ItemGroups
    where_raw  = (m.group(3) or '').strip()   # e.g. Category=51

    # Quote all bare identifiers/values in the WHERE clause.
    # Strategy: tokenise on whitespace, quote tokens that look like
    # column names (pure word, not a number, not AND/OR/IN/IS/NULL/NOT).
    KEYWORDS = {'AND', 'OR', 'IN', 'IS', 'NULL', 'NOT', 'LIKE', 'ILIKE',
                'BETWEEN', 'EXISTS', 'TRUE', 'FALSE'}

    def _quote_token(tok):
        """Quote a single WHERE token if it's a bare identifier."""
        # Keep operators, numbers, quoted strings, parentheses untouched
        if re.match(r'^[\(\)=<>!%\',]', tok):
            return tok
        if re.match(r'^\d+(\.\d+)?$', tok):
            return tok
        if tok.upper() in KEYWORDS:
            return tok
        # It's a bare identifier (column name or unquoted string value)
        return '"' + tok + '"'

    if where_raw:
        # Split carefully — keep =, spaces, numbers together
        tokens = re.split(r'(\s+|(?<==)|(?==))', where_raw)
        where_quoted = ''.join(
            _quote_token(t) if re.match(r'^\w+$', t) else t
            for t in tokens
        )
        where_clause = 'WHERE ' + where_quoted
    else:
        where_clause = ''

    sql = (
        'SELECT "{id}","{lbl}" FROM "{tbl}" {wh} ORDER BY 2'
    ).format(
        id  = id_field.strip('"'),
        lbl = label_col.strip('"'),
        tbl = table_name.strip('"'),
        wh  = where_clause,
    )

    return sql