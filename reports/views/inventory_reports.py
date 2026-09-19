# reports/views/inventory_reports.py
import json
import logging
from django.shortcuts import render
from django.db import connections
from common.middleware.database_middleware import get_customer_db
from common.theme_constants import tb
from common.views.decorators import login_required
from inventory.models.item import ensure_inventory_items_table
from inventory.models.stock import ensure_stocks_table

logger = logging.getLogger(__name__)


@login_required
def stock_report(request):
    """
    Renders the Stock Report view with inventory items, stock valuations,
    and configured interactive report options.

    Parameters:
        request (HttpRequest): The Django HTTP request object.

    Returns:
        HttpResponse: Rendered stock report template with report config and rows.
    """
    db_alias = get_customer_db()
    
    # Ensure tables exist
    try:
        ensure_inventory_items_table(db_alias)
        ensure_stocks_table(db_alias)
    except Exception as e:
        logger.warning("Table check failed: %s", e)
        
    rows = []
    try:
        with connections[db_alias].cursor() as cur:
            # Fetch inventory items with stock information
            cur.execute('''
                SELECT 
                    i."ItemID",
                    i."ItemName",
                    i."ItemCode",
                    COALESCE(NULLIF(i."Unit1Barcode", ''), NULLIF(i."AssortedBarcode", ''), '') AS "Barcode",
                    COALESCE(
                        (SELECT s."Rate1" FROM "Stocks" s WHERE s."ItemID" = i."ItemID" ORDER BY s."Rate1" DESC LIMIT 1),
                        i."MRP", 
                        0
                    ) AS "Retail",
                    0 AS "Qty"
                FROM "InventoryItems" i
                ORDER BY i."ItemID" ASC
            ''')
            cols = [d[0] for d in cur.description]
            for idx, r in enumerate(cur.fetchall(), start=1):
                item_dict = dict(zip(cols, r))
                rows.append({
                    'id': item_dict.get('ItemID'),
                    'slno': idx,
                    'item_name': item_dict.get('ItemName') or '',
                    'item_code': item_dict.get('ItemCode') or '',
                    'barcode': str(item_dict.get('Barcode') or ''),
                    'qty': float(item_dict.get('Qty') or 0),
                    'retail': float(item_dict.get('Retail') or 0),
                })
    except Exception as e:
        logger.error("stock_report query failed: %s", e, exc_info=True)
        rows = []
    
    # Configure report structure matching stock.png and sas-erp report specifications
    report_cfg = {
        'id': 'stock-report',
        'form_id': 'stock-report',
        'title': 'Stock Report',
        'mr_name': 'StockReport',
        'close_onclick': 'history.back()',
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
            {'key': 'slno', 'label': 'SlNo', 'type': 'number', 'width': 60, 'align': 'center'},
            {'key': 'item_name', 'label': 'Item Name', 'type': 'text', 'bold': True, 'width': 420, 'align': 'left'},
            {'key': 'item_code', 'label': 'Item Code', 'type': 'text', 'width': 130, 'align': 'left'},
            {'key': 'barcode', 'label': 'Barcode', 'type': 'text', 'width': 120, 'align': 'left'},
            {'key': 'qty', 'label': 'Qty', 'type': 'number', 'total': True, 'width': 95, 'align': 'right'},
            {'key': 'retail', 'label': 'Retail', 'type': 'number', 'total': True, 'width': 95, 'align': 'right'},
        ],
        'search_fields': [
            {'key': 'item_name', 'label': 'Item Name'},
            {'key': 'item_code', 'label': 'Item Code'},
            {'key': 'barcode', 'label': 'Barcode'},
        ],
        'tile': {
            'titleField': 'item_name',
            'sub1Field': 'item_code',
            'sub2Field': 'barcode',
            'sub3Field': 'retail',
            'pkField': 'id',
        },
    }
    
    context = {
        'r': report_cfg,
        'rows': json.dumps(rows, default=str),
    }
    return render(request, 'reports/stock_report.html', context)
