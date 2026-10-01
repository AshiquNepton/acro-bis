import json
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connections
from common.middleware.database_middleware import get_customer_db
from common.theme_constants import tb
from common.views.decorators import login_required
from common.views.party_master import ensure_party_tables
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)

def _fetch_party_rows(db_alias, mgroup, offset=0, limit=None):
    from core.crud import fetch_tuples
    
    sql = '''
        SELECT 
            c."AccountID",
            c."AcCode",
            c."Description",
            COALESCE(v."Contact", '') AS "Contact",
            COALESCE(v."Mobile", '') AS "Mobile",
            COALESCE(CAST(v."City" AS VARCHAR), '') AS "City",
            COALESCE(v."CreditLimit", 0) AS "CreditLimit"
        FROM "ChartOfAccounts" c
        LEFT JOIN "CustomerVendor" v ON c."AccountID" = v."AccountID"
        WHERE c."MGroup" = %s
        ORDER BY c."AccountID" ASC
    '''
    
    if limit is not None:
        sql += f' LIMIT {int(limit)} OFFSET {int(offset)}'
        
    raw_rows = fetch_tuples(db_alias, sql, [mgroup])
    
    return [
        {
            'id': row[0],
            'slno': idx,
            'ac_code': row[1] or '',
            'name': row[2] or '',
            'contact': row[3] or '',
            'mobile': row[4] or '',
            'city': row[5] or '',
            'credit_limit': float(row[6] or 0),
        }
        for idx, row in enumerate(raw_rows, start=offset + 1)
    ]

def _generate_party_report(request, title, mgroup, form_id):
    db_alias = get_customer_db()
    ensure_party_tables(db_alias)
    
    INITIAL_LIMIT = 100
    rows = []
    
    try:
        rows = _fetch_party_rows(db_alias, mgroup, offset=0, limit=INITIAL_LIMIT)
    except Exception as e:
        logger.error(f"{form_id} query failed: %s", e, exc_info=True)
        
    report_cfg = {
        'id': form_id,
        'form_id': form_id,
        'title': title,
        'mr_name': title.replace(' ', ''),
        'close_onclick': 'history.back()',
        'lazy_load_url': f'/reports/{form_id}/data/',
        'lazy_load_offset': INITIAL_LIMIT,
        'toolbar': [
            tb('Close', 'history.back()', danger=True),
            tb('Save', f"rptRptSave('{form_id}')"),
            tb('Print', f"rptReportPrint('{form_id}')"),
            tb('Design', f"rptRptDesign('{form_id}')"),
            tb('Default', f"rptReportDefault('{form_id}')"),
            tb('Total', f"rptReportTotal('{form_id}')", icon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M16 8h-8l5 4-5 4h8"/></svg>'),
            tb('Options', f"rptOpenReportOptions('{form_id}')", icon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M12 8v8"/><path d="M8 12h8"/></svg>'),
            tb('Refresh', f"rptReportRefresh('{form_id}')"),
        ],
        'menu_items': [
            tb('Export Excel', f"rptExportExcel('{form_id}')"),
            tb('Save PDF', f"rptRptSavePdf('{form_id}')"),
        ],
        'views': ['list', 'grid', 'tiles'],
        'page_size': 50,
        'search_placeholder': f'Search {title.lower()}...',
        'cols': [
            {'key': 'slno', 'label': 'SlNo', 'type': 'number', 'width': 60, 'align': 'center'},
            {'key': 'ac_code', 'label': 'Code', 'type': 'text', 'width': 130, 'align': 'left'},
            {'key': 'name', 'label': 'Name', 'type': 'text', 'bold': True, 'width': 350, 'align': 'left'},
            {'key': 'contact', 'label': 'Contact', 'type': 'text', 'width': 200, 'align': 'left'},
            {'key': 'mobile', 'label': 'Mobile', 'type': 'text', 'width': 120, 'align': 'left'},
            {'key': 'credit_limit', 'label': 'Credit Limit', 'type': 'number', 'total': True, 'width': 100, 'align': 'right'},
        ],
        'search_fields': [
            {'key': 'ac_code', 'label': 'Code'},
            {'key': 'name', 'label': 'Name'},
            {'key': 'contact', 'label': 'Contact'},
            {'key': 'mobile', 'label': 'Mobile'},
        ],
        'tile': {
            'titleField': 'name',
            'sub1Field': 'ac_code',
            'sub2Field': 'contact',
            'sub3Field': 'mobile',
            'pkField': 'id',
        },
    }
    
    context = {
        'page_title': title,
        'r': report_cfg,
        'rows': json.dumps(rows, default=str),
    }
    return render(request, 'reports/generic_report.html', context)

@login_required
def customer_list(request):
    return _generate_party_report(request, 'Customer List', 36, 'customer-list')

@login_required
@require_GET
def customer_list_data(request):
    db_alias = get_customer_db()
    try:
        offset = int(request.GET.get('offset', 0))
        rows = _fetch_party_rows(db_alias, 36, offset=offset, limit=None)
        return JsonResponse({'success': True, 'rows': rows})
    except Exception as e:
        logger.error("customer_list_data failed: %s", e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def vendor_list(request):
    return _generate_party_report(request, 'Vendor List', 37, 'vendor-list')

@login_required
@require_GET
def vendor_list_data(request):
    db_alias = get_customer_db()
    try:
        offset = int(request.GET.get('offset', 0))
        rows = _fetch_party_rows(db_alias, 37, offset=offset, limit=None)
        return JsonResponse({'success': True, 'rows': rows})
    except Exception as e:
        logger.error("vendor_list_data failed: %s", e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})
