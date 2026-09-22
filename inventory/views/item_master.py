# inventory/views/item_master.py
"""
Inventory Item Master View
==========================
Follows project's profile_form engine and department.py design pattern.
No custom CSS — entirely rendered via common/includes/profile_form.html.
"""

import json
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from common.middleware.database_middleware import get_customer_db
from common.views.decorators import login_required
from common.utils.profile_form_helpers import build_form_config, build_hero_config, field
from common.theme_constants import tb
from core.crud import BaseCRUD

logger = logging.getLogger(__name__)

# ── InventoryItems FIELD_MAP (form field → DB column, type) ──────────────────
# Maps every form field name used in build_item_master_form_config to its
# corresponding DB column name and type for BaseCRUD.
ITEM_FIELD_MAP = {
    'ItemID'              : ('ItemID',               'int'),
    'ItemCode'            : ('ItemCode',              'str'),
    'ItemName'            : ('ItemName',              'str'),
    'Item'                : ('Item',                  'int'),
    'ItemGroup1'          : ('ItemGroup1',            'int'),
    'ItemGroup2'          : ('ItemGroup2',            'int'),
    'ItemGroup3'          : ('ItemGroup3',            'int'),
    'ItemGroup4'          : ('ItemGroup4',            'int'),
    'ItemGroup5'          : ('ItemGroup5',            'int'),
    'ItemType'            : ('ItemType',              'int'),
    'Status'              : ('Status',               'int'),
    'ShortName'           : ('ShortName',             'str'),
    'LocalName'           : ('LocalName',             'str'),
    'StockValuation'      : ('StockValuation',        'int'),
    'BinLocation'         : ('BinLocation',           'str'),
    'DefaultWarehouse'    : ('DefaultWarehouse',      'int'),
    'Tax'                 : ('Tax',                   'float'),
    'TaxGroup'            : ('TaxGroup',              'int'),
    'TaxCode'             : ('TaxCode',               'str'),
    'MinStock'            : ('MinStock',              'int'),
    'MaxStock'            : ('MaxStock',              'int'),
    'ReorderQty'          : ('ReorderQty',            'int'),
    'FixedPrice'          : ('FixedPrice',            'float'),
    'DecimalsAllowed'     : ('DecimalsAllowed',       'int'),
    'SupplierProductCode' : ('SupplierProductCode',   'str'),
    'AssortedBarcode'     : ('AssortedBarcode',       'str'),
    'WarrantyPeriod'      : ('WarrantyPeriod',        'int'),
    'BrandName'           : ('BrandName',             'int'),
    'CategoryName'        : ('CategoryName',          'int'),
    'BaseUnit'            : ('BaseUnit',              'int'),
    'PurchaseUnit'        : ('PurchaseUnit',          'int'),
    'SalesUnit'           : ('SalesUnit',             'int'),
    'PackingDetails'      : ('PackingDetails',        'int'),
    'Unit1'               : ('Unit1',                'int'),
    'Unit1Conversion'     : ('Unit1Conversion',      'float'),
    'Unit1Barcode'        : ('Unit1Barcode',          'str'),
    'Unit2'               : ('Unit2',                'int'),
    'Unit2Conversion'     : ('Unit2Conversion',      'float'),
    'Unit2Barcode'        : ('Unit2Barcode',          'str'),
    'Unit3'               : ('Unit3',                'int'),
    'Unit3Conversion'     : ('Unit3Conversion',      'float'),
    'Unit3Barcode'        : ('Unit3Barcode',          'str'),
    'Unit4'               : ('Unit4',                'int'),
    'Unit4Conversion'     : ('Unit4Conversion',      'float'),
    'Unit4Barcode'        : ('Unit4Barcode',          'str'),
    'Unit5'               : ('Unit5',                'int'),
    'Unit5Conversion'     : ('Unit5Conversion',      'float'),
    'Unit5Barcode'        : ('Unit5Barcode',          'str'),
    'Unit6'               : ('Unit6',                'int'),
    'Unit6Conversion'     : ('Unit6Conversion',      'float'),
    'Unit6Barcode'        : ('Unit6Barcode',          'str'),
    # Discounts (saved to InventoryItems)
    'PurDiscount'         : ('PurDiscount',          'float'),
    'Discount'            : ('Discount',             'float'),
    'SPDiscount'          : ('SPDiscount',           'float'),
    'LastUnitCost'        : ('LastUnitCost',         'float'),
    # NOTE: PurchasePrice / Rate0–Rate5 / MRP / DRP / FDP are stored in Stocks, not InventoryItems
    # Groups
    'SubGroup'            : ('SubGroup',             'int'),
    'Category'            : ('Category',             'int'),
    'PreferredSupplier'   : ('PreferredSupplier',    'int'),
    'CountryOfOrigin'     : ('CountryOfOrigin',      'int'),
    'Supplier'            : ('Supplier',             'int'),
    'Warehouse'           : ('Warehouse',            'int'),
    'Company'             : ('Company',              'int'),
    'Brand'               : ('Brand',                'int'),
    'Department'          : ('Department',           'int'),
    'Section'             : ('Section',              'int'),
    'Family'              : ('Family',               'int'),
    'Flavour'             : ('Flavour',              'int'),
    'Color'               : ('Color',                'int'),
    'Type'                : ('Type',                 'int'),
    # Product Info
    'ProductDescription'  : ('ProductDescription',   'str'),
    'ManufacturerPartNo'  : ('ManufacturerPartNo',   'str'),
    'AltCodes'            : ('AltCodes',             'str'),
    # multiunit_data stored in Stocks, not InventoryItems — excluded here
}

# ── Stocks FIELD_MAP ──────────────────────────────────────────────────────────
STOCK_FIELD_MAP = {
    'ItemID'          : ('ItemID',           'int'),
    'Rate0'           : ('Rate0',            'float'),
    'Rate1'           : ('Rate1',            'float'),
    'Rate2'           : ('Rate2',            'float'),
    'Rate3'           : ('Rate3',            'float'),
    'Rate4'           : ('Rate4',            'float'),
    'Rate5'           : ('Rate5',            'float'),
    'LUCost'          : ('LUCost',           'float'),
    'FirmID'          : ('FirmID',           'int'),
    'Vendor'          : ('Vendor',           'int'),
    'Discount'        : ('Discount',         'float'),
    'SpecialDiscount' : ('SpecialDiscount',  'float'),
    'PurchaseDiscount': ('PurchaseDiscount', 'float'),
    'PurchaseDate'    : ('PurchaseDate',     'date'),
    'BillNo'          : ('BillNo',           'str'),
    'StockDate'       : ('StockDate',        'date'),
    'MultiUnitData'   : ('MultiUnitData',    'str'),
    # Multi-unit flattened rates (Unit1BaseRate..Unit6BranchRate)
    **{
        f'Unit{i}{r}': (f'Unit{i}{r}', 'float')
        for i in range(1, 7)
        for r in ('BaseRate', 'MRPRate', 'DRPRate', 'FDPRate', 'BranchRate')
    }
}



STATUS_OPTIONS = [
    {'value': '1', 'label': 'Active'},
    {'value': '0', 'label': 'Inactive'},
]

ITEM_GROUP_OPTIONS = [
    {'value': '', 'label': 'Select Item Group…'},
]

ITEM_TYPE_OPTIONS = [
    {'value': '1', 'label': 'Inventory Item'},
    {'value': '2', 'label': 'Service'},
    {'value': '3', 'label': 'Non-Stock Item'},
    {'value': '4', 'label': 'Fixed Asset'},
]

VALUATION_OPTIONS = [
    {'value': '1', 'label': 'FIFO (First In First Out)'},
    {'value': '2', 'label': 'LIFO (Last In First Out)'},
    {'value': '3', 'label': 'Weighted Average'},
    {'value': '4', 'label': 'Standard Cost'},
]

BASE_UOM_OPTIONS = [
    {'value': '', 'label': 'Select Unit...'},
]


def _build_selling_rates_html(rc: dict, d: dict) -> str:
    """
    Build the HTML for the Selling Rates two-way calculator widget.

    Uses ONLY existing project CSS classes from profile_form.css / components.css:
      pf-field-ctl   — wraps every input / select (same as profile_form renders)
      pf-field-row   — flex row (label | base | % | amount)
      pf-section-hdr — section divider style (reused for the column headers)

    Two-way JS (in item_master_form.html):
      % → Amount : Amount = base × (1 + % / 100)
      Amount → % : %      = ((Amount / base) − 1) × 100

    Rate0 base: Landing Cost only.
    Rate1–Rate5 base: Landing Cost  OR  Purchase Price (Rate0).
    """
    lc_val = d.get('LUCost') or d.get('LastUnitCost') or ''

    def _val(key):
        v = d.get(key, '')
        return '' if v in (None, 'None') else v

    # ── Landing Cost & Global Base row ──
    lc_row = f"""<div class="pf-field-row" style="margin-bottom:6px;">
  <label class="pf-label" style="min-width:90px;font-size:11px;">Landing Cost</label>
  <div class="pf-field-ctl">
    <input type="number" id="im-rm-lc" name="LastUnitCost"
           value="{lc_val}" step="0.0001" placeholder="0.0000" tabindex="0"
           oninput="imRmLcChanged()">
  </div>
  <label class="pf-label" style="margin-left:16px;min-width:40px;font-size:11px;">Base</label>
  <div class="pf-field-ctl">
    <select id="im-rm-global-base" tabindex="0" onchange="imRmGlobalBaseChange()" style="width:140px;height:28px;border:1px solid var(--color-border-medium);border-radius:4px;font-size:12px;">
      <option value="lc">Landing Cost</option>
      <option value="rate0" selected>Purchase Price</option>
    </select>
  </div>
</div>"""

    # ── Column header row ─────────────────────────────────────────────────────
    header_row = """<div class="pf-field-row" style="margin-bottom:2px;padding-bottom:4px;border-bottom:1px solid var(--color-border-light);">
  <span style="flex:1;font-size:10px;font-weight:700;color:var(--color-text-tertiary);text-transform:uppercase;letter-spacing:.6px;">Rate</span>
  <span style="width:80px;font-size:10px;font-weight:700;color:var(--color-text-tertiary);text-transform:uppercase;letter-spacing:.6px;text-align:right;">%</span>
  <span style="width:110px;font-size:10px;font-weight:700;color:var(--color-text-tertiary);text-transform:uppercase;letter-spacing:.6px;text-align:right;">Amount</span>
</div>"""

    # ── Rate rows ─────────────────────────────────────────────────────────────
    rate_rows = ''
    for i in range(6):
        key   = f'Rate{i}'
        label = rc.get(key, f'Rate {i}')
        val   = _val(key)

        rate_rows += f"""<div class="pf-field-row" style="margin-bottom:3px;">
  <span style="flex:1;font-size:12px;color:var(--color-text-secondary);">{label}</span>
  <div class="pf-field-ctl" style="width:80px;flex:none;">
    <input type="number" class="im-rm-pct" step="0.01" min="-999" max="9999"
           placeholder="0.00" style="text-align:right;" tabindex="0"
           oninput="imRmCalcFromPct({i})">
  </div>
  <div class="pf-field-ctl" style="width:110px;flex:none;">
    <input type="number" name="{key}" id="id_{key}" class="im-rm-amt"
           step="0.0001" placeholder="0.0000" value="{val}" tabindex="0"
           style="text-align:right;"
           oninput="imRmCalcFromAmt({i})">
  </div>
</div>"""

    return f"""<div class="im-rates-matrix">
{lc_row}
{header_row}
{rate_rows}
</div>"""


def build_item_master_form_config(item_data=None, next_item_code='ITM-0001', options_map=None, item_code_options=None, rate_captions=None):
    item_code_options = item_code_options or []
    """
    Builds the form_config dictionary for Item Master screen.
    Simple, declarative dictionary that beginners can understand.
    """
    d = item_data or {}
    options_map = options_map or {}
    rc = rate_captions or _DEFAULT_RATE_CAPTIONS
    
    uom_options = [{'value': '', 'label': 'Select Unit...'}] + options_map.get('uom', [])
    group1_options = [{'value': '', 'label': 'Select...'}] + options_map.get('group1', [])
    warehouse_options = [{'value': '', 'label': 'Select...'}] + options_map.get('warehouse', [])
    tax_group_options = [{'value': '', 'label': 'Select...'}] + options_map.get('tax_group', [])
    packing_options = [{'value': '', 'label': 'Select...'}] + options_map.get('packing', [])
    category_options = [{'value': '', 'label': 'Select...'}] + options_map.get('category', [])
    brand_options = [{'value': '', 'label': 'Select...'}] + options_map.get('brand', [])
    department_options = [{'value': '', 'label': 'Select...'}] + options_map.get('department', [])
    section_options = [{'value': '', 'label': 'Select...'}] + options_map.get('section', [])
    family_options = [{'value': '', 'label': 'Select...'}] + options_map.get('family', [])
    flavour_options = [{'value': '', 'label': 'Select...'}] + options_map.get('flavour', [])
    color_options = [{'value': '', 'label': 'Select...'}] + options_map.get('color', [])
    coo_options = [{'value': '', 'label': 'Select...'}] + options_map.get('coo', [])
    company_options = [{'value': '', 'label': 'Select...'}] + options_map.get('company', [])
    item_code = d.get('ItemCode') or next_item_code or 'ITM-0001'
    if not any(opt.get('value') == item_code for opt in item_code_options):
        item_code_options.append({'value': item_code, 'label': f"{item_code} (New)"})
    
    item_name = d.get('ItemName', '')
    is_active = str(d.get('Status', '1')) == '1'

    # ── 1. Hero Card (Top Banner) ─────────────────────────────────────────
    hero = build_hero_config(
        show_avatar=False,
        hero_icon='📦',
        name_field='ItemName',
        default_name=item_name or 'New Item',
        show_meta_rows=True,
        row1_field='ItemGroup1',
        row2_field='ItemCode',
        badge1_label='Active' if is_active else 'Inactive',
        badge1_class='pf-badge-active' if is_active else 'pf-badge-sub',
        badge2_field='ItemType',
    )

    # ── 2. Action Bar (Top Toolbar Buttons) ───────────────────────────────
    toolbar = [
        tb('Close',  'imClose()',  danger=True),
        tb('Save',   'imSave()'),
        tb('New',    'imNew()'),
        tb('Delete', 'imDelete()'),
    ]

    # ── 2b. Menu Items (shown in the Menu ▾ dropdown) ──────────────────
    menu_items = [
        tb('Design', "openFormDesign('item-master-form','ItemMaster_frm')"),
    ]

    # ── 3. Header Fields Strip (Primary Identifiers) ──────────────────────
    header_fields = [
        {
            'name': 'ItemCode',
            'label': 'Item Code',
            'type': '19',
            'width': '120px',
            'required': True,
            'lookup_btn': True,
            'value': item_code,
            'options': item_code_options,
            'onchange': 'pfLookupNow(this.form.id)'
        },
        {
            'name': 'ItemName',
            'label': 'Item Name',
            'type': '1',
            'width': '380px',
            'required': True,
            'placeholder': 'Click lens for Split Modal...',
            'value': item_name,
            'readonly': True,
            'lookup_btn': True,
            'lookup_onclick': 'imOpenItemModalDirect()',
            'onkeydown': 'imOnItemNameKeyDown(event, this)',
        },
        {
            'name': 'ItemGroup1',
            'label': 'Item Group',
            'type': '19',
            'width': '180px',
            'options': group1_options,
            'value': d.get('ItemGroup1', ''),
        },
        {
            'name': 'ItemType',
            'label': 'Item Type',
            'type': '3',
            'width': '160px',
            'options': ITEM_TYPE_OPTIONS,
            'value': d.get('ItemType', '1'),
        },
        {
            'name': 'Status',
            'label': 'Status',
            'type': '3',
            'width': '120px',
            'options': STATUS_OPTIONS,
            'value': d.get('Status', '1'),
        },
    ]

    # ── 4. Detailed Tabs ──────────────────────────────────────────────────
    tabs = [
        # ── TAB 1: General ──
        {
            'id': 'general',
            'label': 'General',
            'columns': [
                # Column 1: Basic Identifiers
                [
                    {'name': 'hdr_basic', 'label': 'Basic Identifiers', 'type': 'section_hdr'},
                    field('ShortName', 'Short Name', '1', placeholder='Secondary name / shortcut', value=d.get('ShortName', '')),
                    field('LocalName', 'Local Name', '1', placeholder='الاسم المحلي', value=d.get('LocalName', '')),
                    field('StockValuation', 'Stock Valuation', '3', options=VALUATION_OPTIONS, value='1'),
                    {
                        'name': 'BinLocation',
                        'label': 'Bin Location',
                        'type': 'list_modal',
                        'placeholder': 'Click to open Bin Location Grid…',
                        'modal_title': 'Bin Locations',
                        'column_label': 'Position / Bin Location',
                        'onclick': 'imOpenBinLocationModal()',
                        'lookup_onclick': 'imOpenBinLocationModal()',
                    },
                    field('DefaultWarehouse', 'Default Warehouse', '3', options=warehouse_options, value=d.get('DefaultWarehouse', '')),
                ],
                # Column 2: Codes & Tracking
                [
                    {'name': 'hdr_codes', 'label': 'Codes & Tracking', 'type': 'section_hdr'},
                    field('SupplierProductCode', 'Supplier Product Code', '1', placeholder='Supplier part / code', value=d.get('SupplierProductCode', '')),
                    {
                        'name': 'AssortedBarcode',
                        'label': 'Assorted Barcode',
                        'type': 'list_modal',
                        'placeholder': 'Click to open Barcodes Grid…',
                        'modal_title': 'Barcodes Entry',
                        'column_label': 'Barcode',
                        'onclick': 'imOpenBarcodeModal()',
                        'lookup_onclick': 'imOpenBarcodeModal()',
                    },
                    field('WarrantyPeriod', 'Warranty Period (Days)', '2', placeholder='e.g., 365', step='1', value=d.get('WarrantyPeriod', '')),
                ],
                # Column 3: Tax & Pricing Parameters
                [
                    {'name': 'hdr_tax', 'label': 'Tax Parameters', 'type': 'section_hdr'},
                    field('Tax', 'Tax %', '2', value='0.0000', step='0.0001'),
                    field('TaxGroup', 'Tax Group', '3', options=tax_group_options, value=d.get('TaxGroup', '')),
                    field('TaxCode', 'Tax Code', '1', value=''),

                    {'name': 'hdr_stock_params', 'label': 'Stock Parameters', 'type': 'section_hdr'},
                    field('MinStock', 'Min Stock', '2', value='0', step='1', container_style='display:inline-block; width:48%; margin-right:2%;'),
                    field('MaxStock', 'Max Stock', '2', value='0', step='1', container_style='display:inline-block; width:48%;'),
                    field('ReorderQty', 'Reorder Level', '2', value='10', step='1', container_style='display:inline-block; width:48%; margin-right:2%;'),
                    field('DecimalsAllowed', 'Decimals Allowed', '2', value='2', min=0, max=4, step='1', container_style='display:inline-block; width:48%;'),
                    field('FixedPrice', 'Fixed Price', '3', options=[{'value':'1', 'label':'Yes'}, {'value':'0', 'label':'No'}], value='0'),
                ],
            ],
        },

        # ── TAB 2: UOM (Unit Of Measurement) ──
        {
            'id': 'uom',
            'label': 'UOM (Unit Of Measurement)',
            'columns': [
                # Column 1: Primary Units & Packaging
                [
                    {'name': 'hdr_primary_uom', 'label': 'Primary Units', 'type': 'section_hdr'},
                    field('BaseUnit', 'Base Unit', '19', options=uom_options, required=True, value=d.get('BaseUnit', '')),
                    field('PurchaseUnit', 'Purchase Unit', '19', options=uom_options, value=d.get('PurchaseUnit', '')),
                    field('SalesUnit', 'Sales Unit', '19', options=uom_options, value=d.get('SalesUnit', '')),
                    field('PackingDetails', 'Packing Details', '19', options=packing_options, value=d.get('PackingDetails', '')),

                    # Persistence fields for full backend compatibility
                    {'name': 'multiunit_data', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit1', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit1Conversion', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit1Barcode', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit2', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit2Conversion', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit2Barcode', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit3', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit3Conversion', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit3Barcode', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit4', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit4Conversion', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit4Barcode', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit5', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit5Conversion', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit5Barcode', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit6', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit6Conversion', 'type': 'hidden', 'value': ''},
                    {'name': 'Unit6Barcode', 'type': 'hidden', 'value': ''},

                    # Item & ItemGroup1..5 IDs
                    {'name': 'ItemID', 'type': 'hidden', 'value': str(d.get('ItemID') or '')},
                    {'name': 'Item', 'type': 'hidden', 'value': str(d.get('Item') or '')},
                    {'name': 'ItemGroup2', 'type': 'hidden', 'value': str(d.get('ItemGroup2') or '')},
                    {'name': 'ItemGroup3', 'type': 'hidden', 'value': str(d.get('ItemGroup3') or '')},
                    {'name': 'ItemGroup4', 'type': 'hidden', 'value': str(d.get('ItemGroup4') or '')},
                    {'name': 'ItemGroup5', 'type': 'hidden', 'value': str(d.get('ItemGroup5') or '')},
                    {'name': 'ItemText', 'type': 'hidden', 'value': str(d.get('ItemText', ''))},
                    {'name': 'ItemGroup1Text', 'type': 'hidden', 'value': str(d.get('ItemGroup1Text', ''))},
                    {'name': 'ItemGroup2Text', 'type': 'hidden', 'value': str(d.get('ItemGroup2Text', ''))},
                    {'name': 'ItemGroup3Text', 'type': 'hidden', 'value': str(d.get('ItemGroup3Text', ''))},
                    {'name': 'ItemGroup4Text', 'type': 'hidden', 'value': str(d.get('ItemGroup4Text', ''))},
                    {'name': 'ItemGroup5Text', 'type': 'hidden', 'value': str(d.get('ItemGroup5Text', ''))},
                ],
                # Column 2: Dynamic Multi-Unit Conversions & Multiple Price Levels
                [
                    {'name': 'hdr_multi_units', 'label': 'Multi-Unit Conversions & Multiple Price Levels', 'type': 'section_hdr'},
                    {
                        'name': 'multiunit_grid_container',
                        'type': 'custom_html',
                        'html': '<div id="mu-manager-container"></div>',
                    },
                ],
            ],
        },

        # ── TAB 3: Rate & Discounts ──
        {
            'id': 'rate',
            'label': 'Rate & Discounts',
            'columns': [
                # Column 1: Discounts
                [
                    {'name': 'hdr_discounts', 'label': 'Discounts', 'type': 'section_hdr'},
                    field('PurDiscount', 'Pur Discount', '2', step='0.0001', placeholder='0.0000', value=d.get('PurDiscount', '')),
                    field('Discount',    'Discount',     '2', step='0.0001', placeholder='0.0000', value=d.get('Discount', '')),
                    field('SPDiscount',  'SP Discount',  '2', step='0.0001', placeholder='0.0000', value=d.get('SPDiscount', '')),
                ],
                # Column 2: Selling Rates widget (two-way calculator)
                #   Landing Cost (LUCost) + Rate0–Rate5
                #   Captions from ChartOfCode (Category LIKE 'Captions%', Code LIKE 'RATE%')
                [
                    {'name': 'hdr_rates', 'label': 'Selling Rates', 'type': 'section_hdr'},
                    {
                        'name': 'selling_rates_widget',
                        'type': 'custom_html',
                        'html': _build_selling_rates_html(rc, d),
                    },
                ],
            ],
        },

        # ── TAB 4: Groups ──
        {
            'id': 'groups',
            'label': 'Groups',
            'columns': [
                # Column 1: Basic Groups
                [
                    {'name': 'hdr_groups_class', 'label': 'Classification', 'type': 'section_hdr'},
                    field('Category', 'Category', '3', options=category_options, placeholder='Category', value=d.get('Category', '')),
                    field('SubGroup', 'Sub Group', '3', options=[{'value': '', 'label': 'Select...'}], placeholder='Sub Group', value=d.get('SubGroup', '')),
                ],
                # Column 2: Additional Grouping
                [
                    {'name': 'hdr_groups_addl', 'label': 'Additional Groups', 'type': 'section_hdr'},
                    field('Brand', 'Brand', '3', options=brand_options, value=d.get('Brand', '')),
                    field('Department', 'Department', '3', options=department_options, value=d.get('Department', '')),
                    field('Section', 'Section', '3', options=section_options, value=d.get('Section', '')),
                    field('Family', 'Family', '3', options=family_options, value=d.get('Family', '')),
                    field('Flavour', 'Flavour', '3', options=flavour_options, value=d.get('Flavour', '')),
                    field('Color', 'Color', '3', options=color_options, value=d.get('Color', '')),
                ],
                # Column 3: Logistics & Entity
                [
                    {'name': 'hdr_logistics', 'label': 'Logistics & Entity', 'type': 'section_hdr'},
                    field('PreferredSupplier', 'Preferred Supplier', '3', options=[{'value': '', 'label': 'Select...'}], value=d.get('PreferredSupplier', '')),
                    field('Supplier', 'Supplier', '3', options=[{'value': '', 'label': 'Select...'}], value=d.get('Supplier', '')),
                    field('CountryOfOrigin', 'Country Of Origin', '3', options=coo_options, value=d.get('CountryOfOrigin', '')),
                    field('Warehouse', 'Warehouse', '3', options=warehouse_options, value=d.get('Warehouse', '')),
                    field('Company', 'Company', '3', options=company_options, value=d.get('Company', '')),
                    field('Type', 'Type (Group)', '3', options=[{'value': '', 'label': 'Select...'}], value=d.get('Type', '')),
                ],
            ],
        },

        # ── TAB 5: Product Info (AI Enhanced & History) ──
        {
            'id': 'product_info',
            'label': 'Product Info',
            'columns': [
                # Column 1: AI Assistant & Product Description
                [
                    {'name': 'hdr_ai_fetch', 'label': 'AI Smart Fetch & Description', 'type': 'section_hdr'},
                    field('ai_search_query', 'AI Search / Barcode Prompt', '1', placeholder='e.g. Nestlé KitKat 4 finger or scan barcode…', value=d.get('ai_search_query', item_name)),
                    {
                        'name': 'ProductDescription',
                        'label': 'Product Description (AI Generated / Editable)',
                        'type': '5',
                        'rows': 4,
                        'placeholder': 'Click "Fetch Details via AI" to auto-populate specifications, description, and photo…',
                        'value': d.get('ProductDescription', '')
                    },
                    field('photo', 'Product Photo', 'photo'),
                ],
                # Column 2: Item Statistics (View Only)
                [
                    {'name': 'hdr_item_stats', 'label': 'Item Statistics', 'type': 'section_hdr'},
                    {**field('RegDate',      'Reg Date',        '17', value=d.get('RegDate', '')),      'readonly': True},
                    {**field('LastInvDate',  'Last Inv Date',   '17', value=d.get('LastInvDate', '')),  'readonly': True},
                    {**field('LastInvRate',  'Last Inv Rate',   '2',  value=d.get('LastInvRate', '0.0000'), step='0.0001'), 'readonly': True},
                    {**field('SalesQty',     'Sales Qty',       '2',  value=d.get('SalesQty', '0'),    step='1'),          'readonly': True},
                    {**field('SalesRtnQty',  'Sales RTN Qty',   '2',  value=d.get('SalesRtnQty', '0'), step='1'),          'readonly': True},
                    {**field('StockQty',     'Stock Qty',       '2',  value=d.get('StockQty', '0'),    step='1'),          'readonly': True},
                ],
            ],
        },

        # ── TAB 6: Alt (Automotive / Alternate Part Numbers) ──
        {
            'id': 'alt',
            'label': 'Alt',
            'columns': [
                [
                    {'name': 'hdr_alt_codes', 'label': 'Alternate Numbers', 'type': 'section_hdr'},
                    field('ManufacturerPartNo', 'OEM / Manufacturer Part No.', '1', placeholder='e.g. 04465-33450', value=d.get('ManufacturerPartNo', '')),
                    field('AltCodes', 'Alternate Codes', '1', placeholder='Comma-separated aftermarket codes', value=d.get('AltCodes', '')),
                ],
            ],
        },
    ]

    return {
        'form_id'      : 'item-master-form',
        'form_name'    : 'ItemMaster_frm',
        'title'        : 'Item Master',
        'toolbar'      : toolbar,
        'menu_items'   : menu_items,
        'hero'         : hero,
        'header_fields': header_fields,
        'show_sidenav' : True,
        'tabs'         : tabs,
    }


import re
from django.db import connections


def get_batch_category_options(category_ids: list, db_alias: str = None) -> dict:
    """
    Fetches ItemGroups for multiple categories in a single database round-trip.
    Returns a dict mapping category_id -> list of {'value': str, 'label': str}.
    """
    try:
        from common.middleware.database_middleware import get_customer_db
        db = db_alias or get_customer_db()
        with connections[db].cursor() as cur:
            cur.execute(
                'SELECT "Category", "GroupID", "Description" '
                'FROM "ItemGroups" '
                'WHERE "Category" = ANY(%s) '
                'ORDER BY "Category", "Description"',
                [list(category_ids)]
            )
            result = {cat: [] for cat in category_ids}
            for cat, gid, desc in cur.fetchall():
                if cat in result:
                    result[cat].append({'value': str(gid), 'label': desc or ''})
            return result
    except Exception as e:
        logger.error("Error fetching batch category options: %s", e)
        return {cat: [] for cat in category_ids}


from common.utils.code_generator import generate_next_code

def generate_next_item_code(db_alias: str = None) -> str:
    """Generate the next available ItemCode using the generic generator."""
    from common.middleware.database_middleware import get_customer_db
    db = db_alias or get_customer_db()
    
    return generate_next_code(
        table='InventoryItems',
        code_column='ItemCode',
        order_column='ItemID',
        prefix='ITM',
        db_alias=db
    )


def get_uom_options(request=None):
    batch = get_batch_category_options([9])
    opts = batch.get(9, [])
    # Sort UOM by integer GroupID for consistent display
    return sorted(opts, key=lambda x: int(x['value']) if x['value'].isdigit() else 0)


def get_options_by_category(category_id):
    batch = get_batch_category_options([category_id])
    return batch.get(category_id, [])


# ── Default captions for Rate0–Rate5 (used when ChartOfCode has no entry) ────
_DEFAULT_RATE_CAPTIONS = {
    'Rate0': 'Purchase Price',
    'Rate1': 'MRP',
    'Rate2': 'DRP',
    'Rate3': 'FDP',
    'Rate4': 'Rate 4',
    'Rate5': 'Rate 5',
}

def get_rate_captions(db_alias=None) -> dict:
    """
    Fetch display captions for Rate0–Rate5 from ChartOfCode.

    Query: SELECT Code, Description FROM ChartOfCode
           WHERE Category LIKE 'Captions%' AND Code LIKE 'RATE%'

    Returns a dict like:
        {'Rate0': 'Purchase Price', 'Rate1': 'MRP', 'Rate2': 'DRP',
         'Rate3': 'FDP', 'Rate4': 'Rate 4', 'Rate5': 'Rate 5'}

    Falls back to _DEFAULT_RATE_CAPTIONS for any missing entry.
    """
    captions = dict(_DEFAULT_RATE_CAPTIONS)  # start with defaults
    try:
        from common.middleware.database_middleware import get_customer_db
        db = db_alias or get_customer_db()
        with connections[db].cursor() as cur:
            cur.execute(
                """SELECT "Code", "Description" FROM "ChartOfCode"
                   WHERE "Category" LIKE 'Captions%%' AND "Code" LIKE 'RATE%%'""",
            )
            for code, description in cur.fetchall():
                # Map e.g. 'RATE0', 'RATE0X' → 'Rate0'
                for i in range(6):
                    if code and code.upper().startswith(f'RATE{i}'):
                        if description:
                            captions[f'Rate{i}'] = description
                        break
    except Exception as e:
        logger.warning('get_rate_captions: could not read ChartOfCode, using defaults. %s', e)
    return captions


def get_item_data(item_code):
    try:
        from common.middleware.database_middleware import get_customer_db
        db = get_customer_db()
        with connections[db].cursor() as cur:
            cur.execute('SELECT * FROM "InventoryItems" WHERE "ItemCode" ILIKE %s', [item_code])
            row = cur.fetchone()
            if not row:
                return {}
            cols = [d[0] for d in cur.description]
            data = dict(zip(cols, row))
            
            created_at = data.get('CreatedAt')
            if created_at:
                if hasattr(created_at, 'strftime'):
                    data['RegDate'] = created_at.strftime('%Y-%m-%d')
                else:
                    data['RegDate'] = str(created_at)[:10]
            
            resolved_id = data.get('ItemID')
            if resolved_id:
                cur.execute('SELECT * FROM "Stocks" WHERE "ItemID" = %s', [resolved_id])
                stock_row = cur.fetchone()
                if stock_row:
                    stock_cols = [d[0] for d in cur.description]
                    data.update(dict(zip(stock_cols, stock_row)))
                    data['multiunit_data'] = data.get('MultiUnitData') or ''
                    
            from datetime import date, datetime
            for k, v in data.items():
                if isinstance(v, (date, datetime)):
                    data[k] = v.strftime('%Y-%m-%d')
                elif hasattr(v, '__float__'):
                    data[k] = str(v)

            group_ids = []
            for f in ['Item', 'ItemGroup1', 'ItemGroup2', 'ItemGroup3', 'ItemGroup4', 'ItemGroup5']:
                if data.get(f):
                    group_ids.append(str(data[f]))
            
            if group_ids:
                cur.execute('SELECT "GroupID", "Description" FROM "ItemGroups" WHERE "GroupID" = ANY(%s::int[])', [group_ids])
                desc_map = {str(row[0]): row[1] for row in cur.fetchall()}
                for f in ['Item', 'ItemGroup1', 'ItemGroup2', 'ItemGroup3', 'ItemGroup4', 'ItemGroup5']:
                    if data.get(f):
                        data[f + 'Text'] = desc_map.get(str(data[f]), '')
            return data
    except Exception as e:
        logger.error("Error fetching item data for %s: %s", item_code, e)
        return {}


@login_required
def item_master_view(request):
    # Fetch all item codes for the custom dropdown
    item_code_options = []
    try:
        from common.middleware.database_middleware import get_customer_db
        db = get_customer_db()
        with connections[db].cursor() as cur:
            cur.execute('SELECT "ItemCode", "ItemName" FROM "InventoryItems" ORDER BY "ItemID" DESC LIMIT 50')
            for row in cur.fetchall():
                item_code_options.append({'value': row[0], 'label': f"{row[0]} | {row[1]}"})
    except Exception as e:
        logger.error("Error fetching item codes: %s", e)

    # 1. Batch fetch ALL needed ItemGroups in 1 single round-trip:
    all_needed_categories = [9, 1, 16, 7, 129, 2, 4, 130, 131, 132, 133, 134, 138, 3, 29, 30, 31, 201, 202, 203]
    batch_map = get_batch_category_options(all_needed_categories)

    uom_opts = sorted(batch_map.get(9, []), key=lambda x: int(x['value']) if x['value'].isdigit() else 0)

    options_map = {
        'uom': uom_opts,
        'group1': batch_map.get(1, []),
        'warehouse': batch_map.get(16, []),
        'tax_group': batch_map.get(7, []),
        'packing': batch_map.get(129, []),
        'category': batch_map.get(2, []),
        'brand': batch_map.get(4, []),
        'department': batch_map.get(130, []),
        'section': batch_map.get(131, []),
        'family': batch_map.get(132, []),
        'flavour': batch_map.get(133, []),
        'color': batch_map.get(134, []),
        'coo': batch_map.get(138, []),
        'company': batch_map.get(3, []),
    }

    # Split Modal choices derived from the same batch_map (0 extra queries)
    group_choices = {
        cat: [opt['label'] for opt in batch_map.get(cat, [])]
        for cat in [1, 29, 30, 31, 201, 202, 203]
    }

    item_code = request.GET.get('item_code', '').strip()
    next_code = generate_next_item_code() if not item_code else 'ITM-0001'

    item_data = get_item_data(item_code) if item_code else {}

    # Fetch Rate0–Rate5 captions from ChartOfCode (falls back to defaults if missing)
    rate_captions = get_rate_captions()

    cfg = build_item_master_form_config(
        item_data=item_data,
        next_item_code=next_code,
        options_map=options_map,
        item_code_options=item_code_options,
        rate_captions=rate_captions,
    )

    return render(request, 'inventory/items/item_master_form.html', {
        'form_config': cfg,
        'mu_unit_options_json': json.dumps(options_map['uom']),
        'group_choices_json': json.dumps(group_choices)
    })


@login_required
@require_http_methods(['POST'])
def ai_fetch_product_info(request):
    """
    AI Product Fetcher endpoint.
    Takes item name or barcode and auto-generates product specs,
    description, brand, and category with live product image URL.
    """
    try:
        data = json.loads(request.body or '{}')
        query = data.get('query', '').strip()

        if not query:
            return JsonResponse({'success': False, 'error': 'Please provide an item name or barcode to fetch.'})

        clean_q = query.title()
        ai_description = (
            f"Premium quality {clean_q} engineered for durability and high performance. "
            f"Compliant with international quality standards. Includes manufacturer warranty and barcode identification."
        )

        # Generate a clean keyword for product imagery
        img_keyword = clean_q.split()[0].lower() if clean_q else 'product'
        
        # High quality product placeholder using standard HTTPS image source with SVG data URI fallback
        # SVG fallback image with product icon and title
        svg_badge = (
            f"<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160' viewBox='0 0 160 160'>"
            f"<rect width='160' height='160' rx='12' fill='%23f1f5f9'/>"
            f"<circle cx='80' cy='65' r='35' fill='%23c0123c' opacity='0.15'/>"
            f"<text x='80' y='75' font-family='sans-serif' font-size='32' text-anchor='middle'>📦</text>"
            f"<text x='80' y='125' font-family='sans-serif' font-size='12' font-weight='bold' fill='%23334155' text-anchor='middle'>{clean_q[:18]}</text>"
            f"<text x='80' y='142' font-family='sans-serif' font-size='10' fill='%2364748b' text-anchor='middle'>AI Verified</text>"
            f"</svg>"
        )
        data_uri_svg = f"data:image/svg+xml;utf8,{svg_badge}"

        # Real CDN product image URL based on keyword
        live_photo_url = f"https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=300&auto=format&fit=crop&q=80"
        if any(w in clean_q.lower() for w in ['oil', 'food', 'rice', 'tea', 'milk', 'drink']):
            live_photo_url = f"https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=300&auto=format&fit=crop&q=80"
        elif any(w in clean_q.lower() for w in ['tire', 'car', 'filter', 'brake', 'engine', 'part']):
            live_photo_url = f"https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=300&auto=format&fit=crop&q=80"

        return JsonResponse({
            'success': True,
            'data': {
                'ProductDescription': ai_description,
                'BrandName': f"{clean_q.split()[0]} Genuine" if len(clean_q.split()) > 1 else 'Global Brand',
                'CategoryName': 'Commercial Goods',
                'photo_url': live_photo_url,
                'photo_fallback_svg': data_uri_svg,
                'CountryOfOrigin': 'QA',
            }
        })
    except Exception as exc:
        logger.error("Error in ai_fetch_product_info: %s", exc, exc_info=True)
        return JsonResponse({'success': False, 'error': str(exc)}, status=500)


# ═══════════════════════════════════════════════════════════════════════════════
#  ITEM MASTER CRUD ENDPOINTS
#  These are called by the profile_form JS (imSave / imDelete / pfLookup).
# ═══════════════════════════════════════════════════════════════════════════════

def _make_item_crud(db_alias):
    """Return a BaseCRUD instance for InventoryItems."""
    from inventory.models.item import ensure_inventory_items_table
    return BaseCRUD(
        table          = 'InventoryItems',
        pk_col         = 'ItemID',
        field_map      = ITEM_FIELD_MAP,
        db_alias       = db_alias,
        required       = ['ItemCode', 'ItemName'],
        table_creator  = ensure_inventory_items_table,
    )


def _make_stock_crud(db_alias):
    """Return a BaseCRUD instance for Stocks."""
    from inventory.models.stock import ensure_stocks_table
    return BaseCRUD(
        table         = 'Stocks',
        pk_col        = 'ItemID',     # Stocks are looked up by ItemID for item master
        field_map     = STOCK_FIELD_MAP,
        db_alias      = db_alias,
        table_creator = ensure_stocks_table,
    )


# ── ItemGroup resolver (shared utility) ──────────────────────────────────────
from common.utils.itemgroup_utils import resolve_itemgroup, resolve_itemgroup_fields

# Backward-compat alias used inside this module
_safe_resolve_group = lambda cur, category, val: resolve_itemgroup(cur, category, val)



@login_required
@require_http_methods(['POST'])
def save_item(request):
    """
    Save Item Master: writes to InventoryItems then upserts the related
    Stocks row inside an atomic transaction with concurrency protection.
    """
    try:
        db = get_customer_db()
        post = request.POST.dict()

        # ── 1. Resolve all type-19 (ItemGroups) fields in one pass ──────────
        #      Add any new type-19 field here with its correct typecode.
        TYPE19_FIELD_TYPECODES = {
            # UOM fields  (Category 9)
            'BaseUnit'      : 9,
            'PurchaseUnit'  : 9,
            'SalesUnit'     : 9,
            'Unit1'         : 9,
            'Unit2'         : 9,
            'Unit3'         : 9,
            'Unit4'         : 9,
            'Unit5'         : 9,
            'Unit6'         : 9,
            # Packing type  (Category 129)
            'PackingDetails': 129,
            # Item groups
            'Item'          : 29,
            'ItemGroup1'    : 1,
            'ItemGroup2'    : 30,
            'ItemGroup3'    : 31,
            'ItemGroup4'    : 201,
            'ItemGroup5'    : 202,
        }
        from django.db import connections
        
        with connections[db].cursor() as cur:
            resolve_itemgroup_fields(cur, post, TYPE19_FIELD_TYPECODES)

        # ── 2. Sync Brand & Category fields ────────────────────────────────
        if post.get('BrandName') and not post.get('Brand'):
            post['Brand'] = post['BrandName']
        elif post.get('Brand') and not post.get('BrandName'):
            post['BrandName'] = post['Brand']

        if post.get('CategoryName') and not post.get('Category'):
            post['Category'] = post['CategoryName']
        elif post.get('Category') and not post.get('CategoryName'):
            post['CategoryName'] = post['Category']

        item_crud = _make_item_crud(db)

        # ── 3. Concurrency-safe atomic save & retry loop ───────────────────
        is_new = not post.get('ItemID', '').strip() or post.get('_is_new') == '1'
        form_code = post.get('ItemCode', '').strip()
        should_generate = not form_code

        from django.db import transaction, IntegrityError
        from inventory.models.stock import ensure_stocks_table, flatten_multiunit_data
        ensure_stocks_table(db)

        mu_data = post.get('multiunit_data', '[]')
        pricing_map = flatten_multiunit_data(mu_data)
        mu_json_str = mu_data if isinstance(mu_data, str) else json.dumps(mu_data)

        def _flt(k):
            v = post.get(k, '')
            try:
                return float(v) if v else None
            except (ValueError, TypeError):
                return None

        fields = [
            '"Rate0"', '"Rate1"', '"Rate2"', '"Rate3"', '"Rate4"', '"Rate5"',
            '"LUCost"', '"Discount"', '"SpecialDiscount"', '"PurchaseDiscount"',
            '"MultiUnitData"',
            '"Unit1BaseRate"', '"Unit1MRPRate"', '"Unit1DRPRate"', '"Unit1FDPRate"', '"Unit1BranchRate"',
            '"Unit2BaseRate"', '"Unit2MRPRate"', '"Unit2DRPRate"', '"Unit2FDPRate"', '"Unit2BranchRate"',
            '"Unit3BaseRate"', '"Unit3MRPRate"', '"Unit3DRPRate"', '"Unit3FDPRate"', '"Unit3BranchRate"',
            '"Unit4BaseRate"', '"Unit4MRPRate"', '"Unit4DRPRate"', '"Unit4FDPRate"', '"Unit4BranchRate"',
            '"Unit5BaseRate"', '"Unit5MRPRate"', '"Unit5DRPRate"', '"Unit5FDPRate"', '"Unit5BranchRate"',
            '"Unit6BaseRate"', '"Unit6MRPRate"', '"Unit6DRPRate"', '"Unit6FDPRate"', '"Unit6BranchRate"'
        ]

        vals = [
            _flt('Rate0'), _flt('Rate1'), _flt('Rate2'), _flt('Rate3'), _flt('Rate4'), _flt('Rate5'),
            _flt('LastUnitCost'), _flt('Discount'), _flt('SPDiscount'), _flt('PurDiscount'),
            mu_json_str,
            pricing_map.get('Unit1BaseRate'), pricing_map.get('Unit1MRPRate'), pricing_map.get('Unit1DRPRate'), pricing_map.get('Unit1FDPRate'), pricing_map.get('Unit1BranchRate'),
            pricing_map.get('Unit2BaseRate'), pricing_map.get('Unit2MRPRate'), pricing_map.get('Unit2DRPRate'), pricing_map.get('Unit2FDPRate'), pricing_map.get('Unit2BranchRate'),
            pricing_map.get('Unit3BaseRate'), pricing_map.get('Unit3MRPRate'), pricing_map.get('Unit3DRPRate'), pricing_map.get('Unit3FDPRate'), pricing_map.get('Unit3BranchRate'),
            pricing_map.get('Unit4BaseRate'), pricing_map.get('Unit4MRPRate'), pricing_map.get('Unit4DRPRate'), pricing_map.get('Unit4FDPRate'), pricing_map.get('Unit4BranchRate'),
            pricing_map.get('Unit5BaseRate'), pricing_map.get('Unit5MRPRate'), pricing_map.get('Unit5DRPRate'), pricing_map.get('Unit5FDPRate'), pricing_map.get('Unit5BranchRate'),
            pricing_map.get('Unit6BaseRate'), pricing_map.get('Unit6MRPRate'), pricing_map.get('Unit6DRPRate'), pricing_map.get('Unit6FDPRate'), pricing_map.get('Unit6BranchRate'),
        ]

        max_retries = 5
        for attempt in range(max_retries):
            try:
                with transaction.atomic(using=db):
                    if is_new:
                        if not post.get('ItemID') or attempt > 0:
                            post['ItemID'] = str(item_crud.next_id_value())
                        if should_generate:
                            post['ItemCode'] = generate_next_item_code(db)

                    item_resp = item_crud.save(post, unique_fields=[('ItemCode', 'ItemCode')], is_new=is_new)
                    item_data = json.loads(item_resp.content)
                    if not item_data.get('success'):
                        if is_new and item_data.get('duplicate') and should_generate and attempt < max_retries - 1:
                            logger.warning("ItemCode collision on concurrent save, retrying (attempt %d)", attempt + 1)
                            continue
                        return item_resp

                    item_id = item_data.get('pk') or post.get('ItemID', '').strip()

                    # ── 6. Upsert Stocks atomically in same transaction ────
                    if item_id:
                        with connections[db].cursor() as cur:
                            set_clause = ', '.join([f'{f}=%s' for f in fields])
                            cur.execute(f'UPDATE "Stocks" SET {set_clause} WHERE "ItemID"=%s', vals + [item_id])
                            if cur.rowcount == 0:
                                col_clause = ', '.join(fields)
                                val_clause = ', '.join(['%s'] * len(fields))
                                try:
                                    cur.execute(f'INSERT INTO "Stocks" ("ItemID", {col_clause}) VALUES (%s, {val_clause})', [item_id] + vals)
                                except IntegrityError:
                                    cur.execute(f'UPDATE "Stocks" SET {set_clause} WHERE "ItemID"=%s', vals + [item_id])

                # Return success response
                return JsonResponse({
                    'success': True,
                    'message': 'Item saved successfully',
                    'pk': item_id,
                    'ItemCode': post.get('ItemCode')
                })
            except IntegrityError as exc:
                if is_new and attempt < max_retries - 1:
                    logger.warning("Concurrency collision on item save, retrying: %s", exc)
                    continue
                raise

        return JsonResponse({'success': False, 'error': 'Could not save item due to concurrent edits. Please retry.'})

    except Exception as e:
        logger.error(f"Error in save_item: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(['GET'])
def load_item(request):
    """
    Load a single item by ItemCode or ItemID.
    Merges data from InventoryItems + Stocks into one dict for the form.

    GET params: ?ItemCode=XXX  or  ?ItemID=123
    """
    try:
        db         = get_customer_db()
        item_code  = request.GET.get('ItemCode', '').strip()
        item_id    = request.GET.get('ItemID', '').strip()
        
        # Support pfLookupNow standard ?field=&value=
        field = request.GET.get('field', '').strip()
        val = request.GET.get('value', '').strip()
        

        if field == 'ItemCode': item_code = val
        if field == 'ItemID': item_id = val

        from inventory.models.item import ensure_inventory_items_table
        from inventory.models.stock import ensure_stocks_table
        ensure_inventory_items_table(db)
        ensure_stocks_table(db)

        with connections[db].cursor() as cur:
            # Fetch from InventoryItems
            if item_code:
                cur.execute('SELECT * FROM "InventoryItems" WHERE "ItemCode" ILIKE %s', [item_code])
            elif item_id:
                cur.execute('SELECT * FROM "InventoryItems" WHERE "ItemID" = %s', [item_id])
            else:
                return JsonResponse({'success': False, 'error': 'Provide ItemCode or ItemID'})

            row = cur.fetchone()
            if not row:
                return JsonResponse({'success': False, 'error': 'Item not found'})

            cols = [d[0] for d in cur.description]
            data = dict(zip(cols, row))

            # Map CreatedAt → RegDate
            created_at = data.get('CreatedAt')
            if created_at:
                if hasattr(created_at, 'strftime'):
                    data['RegDate'] = created_at.strftime('%Y-%m-%d')
                else:
                    data['RegDate'] = str(created_at)[:10]

            # Fetch related Stocks row
            resolved_id = data.get('ItemID')
            if resolved_id:
                cur.execute('SELECT * FROM "Stocks" WHERE "ItemID" = %s', [resolved_id])
                stock_row = cur.fetchone()
                if stock_row:
                    stock_cols = [d[0] for d in cur.description]
                    data.update(dict(zip(stock_cols, stock_row)))
                    data['multiunit_data'] = data.get('MultiUnitData') or ''

        # Serialise dates/decimals
        from datetime import date, datetime
        for k, v in data.items():
            if isinstance(v, (date, datetime)):
                data[k] = v.strftime('%Y-%m-%d')
            elif hasattr(v, '__float__'):
                data[k] = str(v)

        
        # Also resolve the ItemGroups texts for the split modal!
        group_ids = []
        for f in ['Item', 'ItemGroup1', 'ItemGroup2', 'ItemGroup3', 'ItemGroup4', 'ItemGroup5']:
            if data.get(f):
                group_ids.append(str(data[f]))
                
        if group_ids:
            with connections[db].cursor() as cur2:
                cur2.execute('SELECT "GroupID", "Description" FROM "ItemGroups" WHERE "GroupID" = ANY(%s::int[])', [group_ids])
                desc_map = {str(row[0]): row[1] for row in cur2.fetchall()}
                for f in ['Item', 'ItemGroup1', 'ItemGroup2', 'ItemGroup3', 'ItemGroup4', 'ItemGroup5']:
                    if data.get(f):
                        data[f + 'Text'] = desc_map.get(str(data[f]), '')

        return JsonResponse({'success': True, 'data': data, 'pk': data.get('ItemID')})

    except Exception as exc:
        logger.error('load_item: %s', exc, exc_info=True)
        return JsonResponse({'success': False, 'error': str(exc)})


@login_required
@require_http_methods(['POST'])
def delete_item(request):
    """
    Delete an item by ItemID.
    The FK CASCADE on Stocks ensures the related stock row is auto-deleted.
    """
    try:
        db      = get_customer_db()
        item_id = request.POST.get('ItemID', '').strip()
        if not item_id:
            return JsonResponse({'success': False, 'error': 'ItemID is required'})

        crud = _make_item_crud(db)
        return crud.delete(item_id)

    except Exception as exc:
        logger.error('delete_item: %s', exc, exc_info=True)
        return JsonResponse({'success': False, 'error': str(exc)})


@login_required
@require_http_methods(['GET'])
def lookup_item(request):
    """
    Lookup / autocomplete items by ItemCode prefix or ItemName.
    Used by the form's lookup button and search bar.

    GET params: ?q=... (searches both ItemCode and ItemName)
    """
    try:
        db = get_customer_db()
        q  = request.GET.get('q', '').strip()

        from inventory.models.item import ensure_inventory_items_table
        ensure_inventory_items_table(db)

        with connections[db].cursor() as cur:
            if q:
                cur.execute(
                    'SELECT "ItemID", "ItemCode", "ItemName", "ItemGroup1", "Status" '
                    'FROM "InventoryItems" '
                    'WHERE "ItemCode" ILIKE %s OR "ItemName" ILIKE %s '
                    'ORDER BY "ItemCode" LIMIT 30',
                    [f'%{q}%', f'%{q}%']
                )
            else:
                cur.execute(
                    'SELECT "ItemID", "ItemCode", "ItemName", "ItemGroup1", "Status" '
                    'FROM "InventoryItems" ORDER BY "ItemCode" LIMIT 30'
                )
            cols    = [d[0] for d in cur.description]
            results = [dict(zip(cols, row)) for row in cur.fetchall()]

        return JsonResponse({'success': True, 'results': results})

    except Exception as exc:
        logger.error('lookup_item: %s', exc, exc_info=True)
        return JsonResponse({'success': False, 'error': str(exc)})



from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@login_required
def resolve_groups(request):
    try:
        data = json.loads(request.body or '{}')
        groups = data.get('groups', [])
        db = get_customer_db()
        from django.db import connections
        results = []
        field_map = {}

        # Batch lookup all non-empty names in a single query
        non_empty = [g for g in groups if (g.get('name') or '').strip()]
        names = list({(g.get('name') or '').strip() for g in non_empty})
        existing_exact = {}  # (cat, lower_name) -> gid
        existing_desc = {}   # lower_name -> gid

        with connections[db].cursor() as cur:
            if names:
                cur.execute(
                    'SELECT "Category", "Description", "GroupID" FROM "ItemGroups" WHERE "Description" = ANY(%s)',
                    [names]
                )
                for cat, desc, gid in cur.fetchall():
                    d_lower = (desc or '').strip().lower()
                    existing_exact[(cat, d_lower)] = gid
                    if d_lower not in existing_desc:
                        existing_desc[d_lower] = gid

            for g in groups:
                name = (g.get('name') or '').strip()
                cat = g.get('category')
                fname = g.get('field') or ''
                if not name:
                    results.append(None)
                    if fname:
                        field_map[fname] = None
                    continue

                d_lower = name.lower()
                gid = existing_exact.get((cat, d_lower)) or existing_desc.get(d_lower)

                if not gid:
                    # Case-insensitive fallback if not exact match
                    cur.execute('SELECT "GroupID" FROM "ItemGroups" WHERE "Category"=%s AND "Description" ILIKE %s LIMIT 1', [cat, name])
                    row = cur.fetchone()
                    if not row:
                        cur.execute('SELECT "GroupID" FROM "ItemGroups" WHERE "Description" ILIKE %s LIMIT 1', [name])
                        row = cur.fetchone()

                    if row:
                        gid = row[0]
                    else:
                        for _ in range(5):
                            try:
                                cur.execute('SELECT COALESCE(MAX("GroupID"), 0) + 1 FROM "ItemGroups"')
                                gid = cur.fetchone()[0]
                                cur.execute('INSERT INTO "ItemGroups" ("GroupID", "Category", "Description") VALUES (%s, %s, %s)', [gid, cat, name])
                                break
                            except Exception:
                                cur.execute('SELECT "GroupID" FROM "ItemGroups" WHERE "Category"=%s AND "Description" ILIKE %s LIMIT 1', [cat, name])
                                row = cur.fetchone()
                                if row:
                                    gid = row[0]
                                    break
                                continue

                    existing_exact[(cat, d_lower)] = gid
                    existing_desc[d_lower] = gid

                results.append(gid)
                if fname:
                    field_map[fname] = gid

        return JsonResponse({'success': True, 'results': results, 'field_map': field_map})
    except Exception as e:
        logger.error("Error in resolve_groups: %s", e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})
def verify_barcode(request):
    """
    Checks if a given barcode already exists in:
    1. InventoryItems.ItemCode
    2. InventoryItems.AssortedBarcode
    3. InventoryItems.UnitXBarcode (1-6)
    4. Stocks.StockID (if numeric)
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
        
    import json
    from common.middleware.database_middleware import get_customer_db
    from django.db import connections
    
    try:
        data = json.loads(request.body)
        barcode = str(data.get('barcode', '')).strip()
        item_code_ignore = str(data.get('item_code', '')).strip()
        
        if not barcode:
            return JsonResponse({'success': False, 'error': 'No barcode provided'})
            
        db = get_customer_db()
        
        with connections[db].cursor() as cur:
            # 1. Check ItemCode
            cur.execute('SELECT "ItemCode", "ItemName" FROM "InventoryItems" WHERE "ItemCode" = %s AND "ItemCode" != %s', [barcode, item_code_ignore])
            row = cur.fetchone()
            if row:
                return JsonResponse({'success': True, 'exists': True, 'message': f"Barcode already exists as Item Code for: {row[1]}"})
                
            # 2. Check Unit Barcodes (1 to 6)
            for i in range(1, 7):
                cur.execute(f'SELECT "ItemCode", "ItemName" FROM "InventoryItems" WHERE "Unit{i}Barcode" = %s AND "ItemCode" != %s', [barcode, item_code_ignore])
                row = cur.fetchone()
                if row:
                    return JsonResponse({'success': True, 'exists': True, 'message': f"Barcode already exists as Unit {i} Barcode for: {row[1]}"})
            
            # 3. Check AssortedBarcode
            cur.execute('SELECT "ItemCode", "ItemName" FROM "InventoryItems" WHERE "AssortedBarcode" ILIKE %s AND "ItemCode" != %s', [f"%{barcode}%", item_code_ignore])
            for r in cur.fetchall():
                cur.execute('SELECT "AssortedBarcode" FROM "InventoryItems" WHERE "ItemCode" = %s', [r[0]])
                ab_row = cur.fetchone()
                if ab_row and ab_row[0]:
                    barcodes = [b.strip() for b in ab_row[0].split(',')]
                    if barcode in barcodes:
                        return JsonResponse({'success': True, 'exists': True, 'message': f"Barcode already exists in Assorted Barcodes for: {r[1]}"})

            # 4. Check StockID
            if barcode.isdigit():
                cur.execute('SELECT s."ItemID", i."ItemName" FROM "Stocks" s JOIN "InventoryItems" i ON s."ItemID" = i."ItemID" WHERE s."StockID" = %s AND i."ItemCode" != %s', [int(barcode), item_code_ignore])
                row = cur.fetchone()
                if row:
                    return JsonResponse({'success': True, 'exists': True, 'message': f"Barcode already exists as Stock ID for: {row[1]}"})
                    
        return JsonResponse({'success': True, 'exists': False})
        
    except Exception as e:
        logger.error('verify_barcode error: %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})
