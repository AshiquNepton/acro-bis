# reports/views/inventory_reports.py
import json
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connections
from django.views.decorators.http import require_GET
from common.middleware.database_middleware import get_customer_db
from common.theme_constants import tb
from common.views.decorators import login_required
from inventory.models.item import ensure_inventory_items_table
from inventory.models.stock import ensure_stocks_table

logger = logging.getLogger(__name__)

STOCK_REPORT_SQL = '''
    SELECT 
        i."ItemID",
        i."ItemName",
        i."ItemCode",
        COALESCE(NULLIF(i."Unit1Barcode", ''), NULLIF(i."AssortedBarcode", ''), '') AS "Barcode",
        COALESCE(s."Rate1", 0) AS "Retail",
        0 AS "Qty"
    FROM "InventoryItems" i
    LEFT JOIN "Stocks" s ON s."ItemID" = i."ItemID"
    ORDER BY i."ItemID" ASC
'''

def _fetch_rows(db_alias, offset=0, limit=None):
    """Fetch stock report rows from the database with optional offset/limit."""
    from core.crud import fetch_all
    sql = STOCK_REPORT_SQL
    if limit is not None:
        sql += f' LIMIT {int(limit)} OFFSET {int(offset)}'
    
    rows = fetch_all(db_alias, sql)
    
    # Map raw dicts to report expected format
    return [
        {
            'id':        r.get('ItemID'),
            'slno':      idx,
            'item_name': r.get('ItemName') or '',
            'item_code': r.get('ItemCode') or '',
            'barcode':   str(r.get('Barcode') or ''),
            'qty':       float(r.get('Qty') or 0),
            'retail':    float(r.get('Retail') or 0),
        }
        for idx, r in enumerate(rows, start=offset + 1)
    ]


@login_required
def stock_report(request):
    """
    Renders the Stock Report view. Only sends the first 100 rows inline so
    the page paints immediately; the remaining rows are streamed in the
    background via stock_report_data().
    """
    import time
    t0 = time.time()
    db_alias = get_customer_db()

    # Ensure tables exist
    try:
        ensure_inventory_items_table(db_alias)
        ensure_stocks_table(db_alias)
    except Exception as e:
        logger.warning("Table check failed: %s", e)

    # First-paint: only the first 100 rows
    INITIAL_LIMIT = 100
    rows = []
    try:
        rows = _fetch_rows(db_alias, offset=0, limit=INITIAL_LIMIT)
    except Exception as e:
        logger.error("stock_report initial query failed: %s", e, exc_info=True)
        
    t1 = time.time()
    load_time_str = f"{t1 - t0:.3f}"
    logger.info(f"stock_report (first {INITIAL_LIMIT} rows) fetched in {load_time_str} seconds")

    report_cfg = {
        'id': 'stock-report',
        'form_id': 'stock-report',
        'mr_name': 'StockReport',
        'close_onclick': 'history.back()',
        'lazy_load_url': '/reports/stock-report/data/',   # ← background fetch
        'lazy_load_offset': INITIAL_LIMIT,                # ← start after first 100
        'toolbar': [
            tb('Close', 'history.back()', danger=True),
            tb('Save', "rptRptSave('stock-report')"),
            tb('Print', "rptReportPrint('stock-report')"),
            tb('Design', "rptRptDesign('stock-report')"),
            tb('Default', "rptReportDefault('stock-report')"),
            tb('Total', "rptReportTotal('stock-report')", icon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M16 8h-8l5 4-5 4h8"/></svg>'),
            tb('Options', "rptOpenReportOptions('stock-report')", icon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M12 8v8"/><path d="M8 12h8"/></svg>'),
            tb('Refresh', "rptReportRefresh('stock-report')"),
        ],
        'menu_items': [
            tb('Export Excel', "rptExportExcel('stock-report')"),
            tb('Save PDF', "rptRptSavePdf('stock-report')"),
        ],
        'views': ['list', 'grid', 'tiles'],
        'page_size': 50,
        'search_placeholder': 'Search items…',
        'cols': [
            {'key': 'slno',      'label': 'SlNo',      'type': 'number', 'width': 60,  'align': 'center'},
            {'key': 'item_name', 'label': 'Item Name', 'type': 'text',   'bold': True, 'width': 420, 'align': 'left'},
            {'key': 'item_code', 'label': 'Item Code', 'type': 'text',   'width': 130, 'align': 'left'},
            {'key': 'barcode',   'label': 'Barcode',   'type': 'text',   'width': 120, 'align': 'left'},
            {'key': 'qty',       'label': 'Qty',       'type': 'number', 'total': True, 'width': 95, 'align': 'right'},
            {'key': 'retail',    'label': 'Retail',    'type': 'number', 'total': True, 'width': 95, 'align': 'right'},
        ],
        'search_fields': [
            {'key': 'item_name', 'label': 'Item Name'},
            {'key': 'item_code', 'label': 'Item Code'},
            {'key': 'barcode',   'label': 'Barcode'},
        ],
        'tile': {
            'titleField': 'item_name',
            'sub1Field':  'item_code',
            'sub2Field':  'barcode',
            'sub3Field':  'retail',
            'pkField':    'id',
        },
    }

    context = {
        'page_title': 'Stock Report',
        'r':    report_cfg,
        'rows': json.dumps(rows, default=str),
    }
    return render(request, 'reports/stock_report.html', context)


@login_required
@require_GET
def stock_report_data(request):
    """
    Background JSON endpoint. Returns all rows starting from ?offset=N.
    Called by the frontend after the first paint so remaining data loads silently.
    """
    import time
    t0 = time.time()
    db_alias = get_customer_db()
    try:
        offset = int(request.GET.get('offset', 0))
        rows = _fetch_rows(db_alias, offset=offset, limit=None)
        t1 = time.time()
        logger.info(f"stock_report_data (remaining {len(rows)} rows) fetched in {t1 - t0:.4f} seconds")
        return JsonResponse({'success': True, 'rows': rows})
    except Exception as e:
        logger.error("stock_report_data failed: %s", e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


