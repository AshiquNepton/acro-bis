# common/views/department.py
"""
Department / Job master — page view + CRUD endpoints.

Duplicate detection
───────────────────
• Live check  GET /hrms/department/check-duplicate/
  Returns immediately whether a name already exists, used on field blur.

• Hard block  POST /hrms/department/save/
  save_department() calls crud.save(..., unique_fields=[...]) which calls
  BaseCRUD.check_duplicate() before the INSERT/UPDATE.  If a duplicate is
  found the save is aborted and { success:false, duplicate:true, error:… }
  is returned — profile_form.js surfaces this as a toast automatically.

Extending to other forms
────────────────────────
Any view that calls crud.save() can pass unique_fields:

    # Single field
    return crud.save(request.POST, unique_fields=[('FName', 'dept_name')])

    # Compound unique (name + parent)
    return crud.save(request.POST, unique_fields=[
        ('FName', 'dept_name'),
        ('Under', 'under'),
    ])

For a standalone live-check endpoint copy check_duplicate_department() and
swap the field names — the BaseCRUD.check_duplicate() call is the same.
"""

import logging

from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from common.middleware.database_middleware import get_customer_db
from common.models.company_information import Organization
from common.theme_constants import tb
from common.utils.form_helpers import fetch_record_by_field_view, search_records_view
from common.models.firm_master import FirmMaster, ensure_firm_master_table
from common.views.decorators import login_required
from core.crud import BaseCRUD



logger = logging.getLogger(__name__)


# ── Field mappings ────────────────────────────────────────────────────────────

FIRM_FIELD_MAPPING = {
    'FirmID'  : 'firm_id',
    'FName'   : 'dept_name',
    'Under'   : 'under',
    'SubHead' : 'sub_head',
    'FStatus' : 'f_status',
    'Phone'   : 'phone',
    'Address1': 'address1',
    'Address2': 'address2',
    'Address3': 'address3',
}

FRONTEND_TO_DB = {v: k for k, v in FIRM_FIELD_MAPPING.items()}

STATUS_OPTIONS = [
    {'value': '1', 'label': 'Active'},
    {'value': '0', 'label': 'Inactive'},
]

# ── Fields that must be unique (db_col, form_field_name) ─────────────────────
# Change this list to adjust which fields form the duplicate key for departments.
# Examples:
#   Single field only:          [('FName', 'dept_name')]
#   Name must be unique per parent:  [('FName', 'dept_name'), ('Under', 'under')]
DEPT_UNIQUE_FIELDS = [('FName', 'dept_name')]



# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_company_db(request) -> str:
    return get_customer_db()


def _make_crud(db: str) -> BaseCRUD:
    """Convenience: build a BaseCRUD for FirmMaster."""
    return BaseCRUD(
        table         = 'FirmMaster',
        pk_col        = 'FirmID',
        field_map     = FIRM_FIELD_MAPPING,
        db_alias      = db,
        table_creator = ensure_firm_master_table,
    )


def _get_under_options(request) -> list:
    options = [
        {'value': '',  'label': 'Select Parent…'},
        {'value': '0', 'label': '— Top Level (No Parent) —'},
    ]

    try:
        db = get_customer_db()
        ensure_firm_master_table(db)
        depts = (
            FirmMaster.objects
            .using(db)
            .values('FirmID', 'FName')
            .order_by('FName')
        )
        for d in depts:
            options.append({
                'value': str(d['FirmID']),
                'label': d['FName'] or f"#{d['FirmID']}",
            })
    except Exception as exc:
        logger.warning('_get_under_options: could not load departments: %s', exc)

    return options

def _get_dept_options(db: str) -> list:
    options = []
    try:
        ensure_firm_master_table(db)
        depts = (
            FirmMaster.objects.using(db)
            .values('FirmID', 'FName')
            .order_by('FName')
        )
        for d in depts:
            options.append({
                'value': str(d['FirmID']),
                'label': d['FName'] or f"#{d['FirmID']}",
            })
    except Exception as exc:
        logger.warning('_get_dept_options: %s', exc)
    return options

# ── Form config ───────────────────────────────────────────────────────────────

def _build_form_config(under_options=None, next_firm_id=None, dept_options=None):
    under_opts = under_options or [{'value': '', 'label': 'Select Parent…'}]

    return {
        'form_id'  : 'dept-form',
        'form_name': 'Department_frm',
        'title'    : 'Department / Job Master',

        'toolbar': [
            tb('Close',  'dfClose()',  danger=True),
            tb('Save',   'dfSave()'),
            tb('New',    'dfNew()'),
            tb('Delete', 'dfDelete()'),
        ],

        'menu_items': [
            tb('Print',  'deptPrint()'),
            {'sep': True, 'label': '', 'onclick': '', 'danger': False, 'icon': ''},
            tb('Design', "openFormDesign('dept-form','Department_frm')"),
        ],


        # ── Header strip ─────────────────────────────────────────────────────
        'header_fields': [
            {
                'name'      : 'firm_id',
                'label'     : 'Dept./Job ID',
                'type'      : '2',
                'readonly'  : True,
                'required'  : True,
                'width'     : '130px',
                'lookup_btn': True,
                **({'value': str(next_firm_id)} if next_firm_id is not None else {}),
            },
           {
                'name'    : 'dept_name',
                'label'   : 'Dept./Job Name',
                'type'    : '19',
                'required': True,
                'width'   : '420px',
                'options' : [{'value': '', 'label': 'Select Dept./Job…'}] + (dept_options or []),
                'onchange': 'deptNameChanged(this)',
            },
            {
                'name'   : 'under',
                'label'  : 'Under',
                'type'   : '3',
                'width'  : '260px',
                'options': under_opts,
            },
            {
                'name'   : 'f_status',
                'label'  : 'Status',
                'type'   : '3',
                'width'  : '130px',
                'value'  : '1',
                'options': STATUS_OPTIONS,
            },
        ],

        'show_sidenav': False,

        # ── Tabs ─────────────────────────────────────────────────────────────
        'tabs': [
            {
                'id'   : 'general',
                'label': 'General',
                'columns': [
                    [
                        {'name': 'sub_head', 'label': 'Sub Head', 'type': '1'},
                        {'name': 'phone',    'label': 'Phone',    'type': '14'},
                    ],
                    [
                        {'name': 'address1', 'label': 'Address 1', 'type': '1'},
                        {'name': 'address2', 'label': 'Address 2', 'type': '1'},
                        {'name': 'address3', 'label': 'Address 3', 'type': '1'},
                    ],
                ],
            },
        ],
    }


# ── Page view ─────────────────────────────────────────────────────────────────
@login_required
def department_form(request):

    ctx = build_department_context(request, reverse('common:list_departments'))
    ctx['base_template'] = 'common/base.html'
    return render(request, 'common/masters/department_form.html', ctx)


# ── CRUD endpoints ────────────────────────────────────────────────────────────

@require_http_methods(['GET'])
def lookup_department(request):
    """Exact lookup by FirmID."""
    return fetch_record_by_field_view(request, FirmMaster, FIRM_FIELD_MAPPING)


@require_http_methods(['GET'])
def search_department(request):
    """Autocomplete search by department name."""
    return search_records_view(
        request, FirmMaster, 'FName', FIRM_FIELD_MAPPING,
        display_fields=['firm_id', 'dept_name'],
    )


# ── Live duplicate check endpoint ─────────────────────────────────────────────

@require_http_methods(['GET'])
def check_duplicate_department(request):
    """
    Live duplicate check called on field blur from the frontend.

    Query params
    ────────────
    dept_name : str   — the value being typed in the dept name field
    firm_id   : str   — current record's PK (empty / 0 for new records)

    The check always uses DEPT_UNIQUE_FIELDS so it stays in sync with
    what save_department() enforces.

    Response
    ────────
    { "is_duplicate": false }
    { "is_duplicate": true,  "existing_pk": 7,
      "message": "A department named \"Accounts\" already exists (ID: 7)." }
    """
    try:
        db   = _get_company_db(request)
        crud = _make_crud(db)

        # Build the value dict from GET params keyed by form_field_name
        resolved = []
        for db_col, form_field in DEPT_UNIQUE_FIELDS:
            raw_val = request.GET.get(form_field, '').strip()
            resolved.append((db_col, raw_val))

        # Exclude the current record so editing doesn't self-flag
        raw_pk     = request.GET.get('firm_id', '').strip()
        exclude_pk = int(raw_pk) if raw_pk and raw_pk != '0' else None

        result = crud.check_duplicate(resolved, exclude_pk=exclude_pk)

        if result['is_duplicate']:
            # Human-readable field labels for the message
            field_labels = ', '.join(
                f'"{request.GET.get(ff, ff)}"'
                for _, ff in DEPT_UNIQUE_FIELDS
                if request.GET.get(ff, '').strip()
            )
            existing_id = result['existing_pk']
            return JsonResponse({
                'is_duplicate': True,
                'existing_pk' : existing_id,
                'message'     : (
                    f'A department with this name already exists (ID: {existing_id}).'
                ),
            })

        return JsonResponse({'is_duplicate': False})

    except Exception as exc:
        logger.error('check_duplicate_department: %s', exc, exc_info=True)
        # On error, don't block the user — treat as no-duplicate
        return JsonResponse({'is_duplicate': False, 'error': str(exc)})


def save_department(request):
    try:
        db = _get_company_db(request)
        ensure_firm_master_table(db)

        firm_id = request.POST.get('firm_id', '').strip()
        if not firm_id:
            return JsonResponse({'success': False, 'error': 'Dept./Job ID is required'})

        raw_under = request.POST.get('under', '') or ''
        try:
            under_int = int(raw_under) if raw_under else 0
        except ValueError:
            under_int = 0

        raw_dept_name_val = request.POST.get('dept_name', '').strip()
        resolved_fname = None
        if raw_dept_name_val:
            try:
                ref_id = int(raw_dept_name_val)
                ref_firm = FirmMaster.objects.using(db).filter(FirmID=ref_id).values('FName').first()
                if ref_firm:
                    resolved_fname = (ref_firm['FName'] or '').strip() or None
            except (ValueError, TypeError):
                resolved_fname = raw_dept_name_val[:50] or None

        post_data = request.POST.dict()
        post_data['dept_name'] = resolved_fname or ''
        post_data['under'] = str(under_int)
        
        crud = _make_crud(db)
        return crud.save(post_data, unique_fields=DEPT_UNIQUE_FIELDS)

    except Exception as exc:
        logger.error('save_department: %s', exc, exc_info=True)
        return JsonResponse({'success': False, 'error': str(exc)})
    

@require_http_methods(['GET'])
def get_department(request, firm_id):
    """Return a single FirmMaster row as JSON for form population."""
    try:
        db   = _get_company_db(request)
        ensure_firm_master_table(db)

        from django.shortcuts import get_object_or_404
        firm = get_object_or_404(FirmMaster.objects.using(db), FirmID=firm_id)

        data = {}
        for db_field, form_field in FIRM_FIELD_MAPPING.items():
            value = getattr(firm, db_field, None)
            data[form_field] = str(value) if value is not None else None

        under_val = firm.Under
        data['under'] = str(under_val) if under_val and int(under_val) != 0 else ''
        data['dept_name'] = str(firm.FirmID) 


        return JsonResponse({'success': True, 'data': data})

    except Exception as exc:
        logger.error('get_department: %s', exc, exc_info=True)
        return JsonResponse({'success': False, 'error': str(exc)})


@require_http_methods(['POST'])
def delete_department(request, firm_id):
    db = _get_company_db(request)
    return _make_crud(db).delete(firm_id)


@require_http_methods(['GET'])
def list_departments(request):
    """
    Return ALL FirmMaster rows plus company names, as a fully nested tree.
    """
    try:
        db = _get_company_db(request)
        ensure_firm_master_table(db)

        firms_qs = list(
            FirmMaster.objects.using(db)
            .values('FirmID', 'FName', 'Under', 'SubHead', 'FStatus', 'Phone')
            .order_by('FName')
        )

        company_map = {}
        try:
            customer_db = get_customer_db()
            orgs = Organization.objects.using(customer_db).values('CompanyId', 'CompanyName')
            company_map = {o['CompanyId']: o['CompanyName'] for o in orgs}
        except Exception as exc:
            logger.warning('list_departments: could not load company names: %s', exc)

        company_ids = set(company_map.keys())
        firm_ids    = {f['FirmID'] for f in firms_qs}

        def _dept_node(f):
            return {
                'type'    : 'dept',
                'id'      : f['FirmID'],
                'label'   : f['FName'] or f'#{f["FirmID"]}',
                'status'  : 'active' if str(f['FStatus']) == '1' else 'inactive',
                'phone'   : f['Phone']   or '',
                'sub_head': f['SubHead'] or '',
                'under'   : f['Under'],
                'children': [],
            }

        nodes = {f['FirmID']: _dept_node(f) for f in firms_qs}

        company_nodes = {}
        for cid, cname in sorted(company_map.items(), key=lambda x: x[1]):
            company_nodes[cid] = {
                'type'    : 'company',
                'id'      : f'c_{cid}',
                'raw_id'  : cid,
                'label'   : cname,
                'children': [],
            }

        orphans = []
        default_company_id = next(iter(company_nodes), None)

        for f in firms_qs:
            fid   = f['FirmID']
            under = f['Under'] or 0

            if under == 0 and default_company_id is not None:
                company_nodes[default_company_id]['children'].append(nodes[fid])
            elif under in firm_ids and under != fid:
                nodes[under]['children'].append(nodes[fid])
            elif under in company_ids:
                company_nodes[under]['children'].append(nodes[fid])
            else:
                orphans.append(nodes[fid])

        tree = list(company_nodes.values())

        if orphans:
            tree.append({
                'type'    : 'company',
                'id'      : 'c_0',
                'raw_id'  : 0,
                'label'   : '(No Parent)',
                'children': orphans,
            })

        return JsonResponse({'success': True, 'tree': tree})

    except Exception as exc:
        logger.error('list_departments: %s', exc, exc_info=True)
        return JsonResponse({'success': False, 'error': str(exc)})


# ── Shared table config ───────────────────────────────────────────────────────
DEPT_TABLE_CONFIG = {
    'id'        : 'dept-all-table',
    'cols'      : [
        {'key': 'firm_id',   'label': 'ID'},
        {'key': 'dept_name', 'label': 'Department / Job'},
        {'key': 'sub_head',  'label': 'Sub Head'},
        {'key': 'status',    'label': 'Status'},
        {'key': 'phone',     'label': 'Phone'},
    ],
    'toolbar'   : [
        {'label': 'Refresh', 'onclick': 'deptTableLoad()', 'icon': 'refresh'},
    ],
    'note_id'  : 'dept-all-table-note',
    'note_text': 'Loading…',
    'empty_text': 'No departments found.',
}


def build_department_context(request, list_url: str, dept_table=None) -> dict:
    db = _get_company_db(request)
    ensure_firm_master_table(db)

    crud = BaseCRUD(
        table     = 'FirmMaster',
        pk_col    = 'FirmID',
        field_map = FIRM_FIELD_MAPPING,
        db_alias  = db,
    )
    next_firm_id = crud.next_id_value()

    return {
        'form_config': _build_form_config(
            _get_under_options(request),
            next_firm_id,
            _get_dept_options(db),
        ),
        'auto_select_dept': request.GET.get('select', ''),
        'dept_table'      : dept_table if dept_table is not None else DEPT_TABLE_CONFIG,
        'dept_list_url'   : list_url,
    }

@require_http_methods(['GET'])
def get_next_dept_id(request):
    """Return the next available FirmID without creating any record."""
    db = _get_company_db(request)
    ensure_firm_master_table(db)
    crud = BaseCRUD(
        table     = 'FirmMaster',
        pk_col    = 'FirmID',
        field_map = FIRM_FIELD_MAPPING,
        db_alias  = db,
    )
    return JsonResponse({'success': True, 'next_id': crud.next_id_value()})