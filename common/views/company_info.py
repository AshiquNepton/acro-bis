# common/views/company.py
import logging
import os
from datetime import datetime
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from common.middleware.database_middleware import get_customer_db
from common.models.company_information import Organization
from common.utils.form_helpers import fetch_record_by_field_view, search_records_view
from common.theme_constants import tb
from common.views.decorators import login_required

logger = logging.getLogger(__name__)

COMPANY_FIELD_MAPPING = {
    'CompanyId'          : 'company_code',
    'CompanyName'        : 'company_name',
    'ArabicName'         : 'arabic_name',
    'Subtitle'           : 'subtitle',
    'Address1'           : 'address1',
    'Address2'           : 'address2',
    'Address3'           : 'address3',
    'Phone'              : 'phone',
    'Mobile'             : 'mobile',
    'Url'                : 'website',
    'Email'              : 'email',
    'TinNo'              : 'tinno',
    'CrNo'               : 'crno',
    'LicenseNo'          : 'licenseno',
    'BuildingNo'         : 'building_no',
    'StreetName'         : 'street_name',
    'Zone'               : 'zone',
    'Area'               : 'area',
    'City'               : 'city',
    'State'              : 'state',
    'District'           : 'district',
    'PoBox'              : 'po_box',
    'PlotIdentification' : 'plot_identification',
    'AccountNumber'      : 'account_number',
    'AccountName'        : 'account_name',
    'Branch'             : 'branch',
    'Ifsc'               : 'ifsc',
    'PayerId'            : 'payer_id',
    'PayerBank'          : 'payer_bank',
    'PayerIban'          : 'payer_iban',
    'PeriodFrom'         : 'period_from',
    'PeriodTo'           : 'period_to',
    'BusinessType'       : 'business_type',
    'DefaultDb'          : 'default_db',
    'DbName'             : 'db_name',
}

FRONTEND_TO_DB_MAPPING = {v: k for k, v in COMPANY_FIELD_MAPPING.items()}


# ─── Sync helpers ─────────────────────────────────────────────────────────────

def _load_pg_env():
    """
    Load PostgreSQL admin credentials from the project .env file,
    mirroring the pattern used in auth.py / pg_manager.py.
    Returns a dict with keys: host, port, user, password, registry_db.
    """
    env_path = Path(__file__).resolve().parent.parent.parent.parent / '.env'
    load_dotenv(env_path)
    return {
        'host'        : os.getenv('DB_HOST', ''),
        'port'        : os.getenv('PORT', '5432'),
        'user'        : os.getenv('DB_USER', ''),
        'password'    : os.getenv('DB_PASSWORD', ''),
        'registry_db' : os.getenv('DB_NAME', ''),
    }


def _pg_connect(database):
    """
    Open a psycopg2 connection to `database` using admin credentials from .env.
    autocommit=True mirrors pg_manager.py behaviour.
    """
    env = _load_pg_env()
    conn = psycopg2.connect(
        host=env['host'],
        port=env['port'],
        user=env['user'],
        password=env['password'],
        database=database,
        connect_timeout=10,
    )
    conn.autocommit = True
    return conn


def _sync_provisioned_db(company, db_name):
    """
    Sync all editable fields into the company's own provisioned database:
      • Organization  WHERE CompanyId = 1
      • FirmMaster    WHERE FirmID    = 1

    Both updates are best-effort — failures are logged but never raise.
    """
    if not db_name:
        logger.warning('_sync_provisioned_db: db_name is empty, skipping')
        return

    try:
        conn = _pg_connect(db_name)
    except Exception as exc:
        logger.error(
            '_sync_provisioned_db: cannot connect to "%s": %s', db_name, exc
        )
        return

    try:
        cur = conn.cursor()

        # ── Organization ──────────────────────────────────────────────────────
        try:
            cur.execute(
                """
                UPDATE "Organization" SET
                    "CompanyName"        = %s,
                    "ArabicName"         = %s,
                    "Subtitle"           = %s,
                    "Address1"           = %s,
                    "Address2"           = %s,
                    "Address3"           = %s,
                    "Phone"              = %s,
                    "Mobile"             = %s,
                    "Url"                = %s,
                    "Email"              = %s,
                    "TinNo"              = %s,
                    "CrNo"               = %s,
                    "LicenseNo"          = %s,
                    "BuildingNo"         = %s,
                    "StreetName"         = %s,
                    "Zone"               = %s,
                    "Area"               = %s,
                    "City"               = %s,
                    "State"              = %s,
                    "District"           = %s,
                    "PoBox"              = %s,
                    "PlotIdentification" = %s,
                    "AccountNumber"      = %s,
                    "AccountName"        = %s,
                    "Branch"             = %s,
                    "Ifsc"               = %s,
                    "PayerId"            = %s,
                    "PayerBank"          = %s,
                    "PayerIban"          = %s,
                    "PeriodFrom"         = %s,
                    "PeriodTo"           = %s,
                    "DefaultDb"          = %s,
                    "BusinessType"       = %s
                WHERE "CompanyId" = 1
                """,
                (
                    company.CompanyName,
                    company.ArabicName,
                    company.Subtitle,
                    company.Address1,
                    company.Address2,
                    company.Address3,
                    company.Phone,
                    company.Mobile,
                    company.Url,
                    company.Email,
                    company.TinNo,
                    company.CrNo,
                    company.LicenseNo,
                    company.BuildingNo,
                    company.StreetName,
                    company.Zone,
                    company.Area,
                    company.City,
                    company.State,
                    company.District,
                    company.PoBox,
                    company.PlotIdentification,
                    company.AccountNumber,
                    company.AccountName,
                    company.Branch,
                    company.Ifsc,
                    company.PayerId,
                    company.PayerBank,
                    company.PayerIban,
                    company.PeriodFrom,
                    company.PeriodTo,
                    company.DefaultDb,
                    company.BusinessType,
                ),
            )
            logger.info(
                '_sync_provisioned_db: Organization updated in "%s" (rows=%s)',
                db_name, cur.rowcount,
            )
        except Exception as exc:
            logger.error(
                '_sync_provisioned_db: Organization update failed in "%s": %s',
                db_name, exc,
            )

        # ── FirmMaster ────────────────────────────────────────────────────────
        try:
            phone_val = (company.Phone or '')[:10] or None
            cur.execute(
                """
                UPDATE "FirmMaster" SET
                    "FName"    = %s,
                    "Phone"    = %s,
                    "Address1" = %s,
                    "Address2" = %s,
                    "Address3" = %s
                WHERE "FirmID" = 1
                """,
                (
                    company.CompanyName,
                    phone_val,
                    company.Address1,
                    company.Address2,
                    company.Address3,
                ),
            )
            logger.info(
                '_sync_provisioned_db: FirmMaster updated in "%s" (rows=%s)',
                db_name, cur.rowcount,
            )
        except Exception as exc:
            logger.error(
                '_sync_provisioned_db: FirmMaster update failed in "%s": %s',
                db_name, exc,
            )

        cur.close()

    finally:
        conn.close()


def _sync_registry(company, db_name):
    """
    Update the central registry DB's `customers` table for this company.
    Lookup: softwares.db = db_name  →  custid  →  customers.custid
    Fields synced: custname, location (rebuilt from Address1/2/3).
    """
    if not db_name:
        logger.warning('_sync_registry: db_name is empty, skipping')
        return

    location = ', '.join(filter(None, [
        company.Address1 or '',
        company.Address2 or '',
        company.Address3 or '',
    ]))

    try:
        conn = _pg_connect(_load_pg_env()['registry_db'])
    except Exception as exc:
        logger.error('_sync_registry: cannot connect to registry DB: %s', exc)
        return

    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE customers
               SET custname = %s,
                   location = %s
             WHERE custid = (
                 SELECT custid FROM softwares WHERE db = %s LIMIT 1
             )
            """,
            (company.CompanyName, location, db_name),
        )
        logger.info(
            '_sync_registry: customers updated for db="%s" (rows=%s)',
            db_name, cur.rowcount,
        )
        cur.close()
    except Exception as exc:
        logger.error('_sync_registry: customers update failed for db="%s": %s', db_name, exc)
    finally:
        conn.close()


# ─── Form config ──────────────────────────────────────────────────────────────

def _build_form_config(company_options=None, business_type=None):
    current_year = datetime.now().year

    dropdown_options = [{'value': '', 'label': '— Select Company —'}]
    if company_options:
        dropdown_options += company_options

    header_fields = [
        {
            'name'     : 'company_code',
            'label'    : 'Company Code',
            'type'     : '2',
            'required' : True,
            'width'    : '120px',
            'readonly' : True,          # not editable — system identifier
        },
        {
            'name'     : 'company_name',
            'label'    : 'Company Name',
            'type'     : '1',
            'required' : True,
            'width'    : '600px',
        },
        {
            'name'  : 'business_type',
            'label' : '',
            'type'  : '18',
            'value' : str(business_type) if business_type else '1',
        },
    ]

    tabs = [
        {
            'id': 'general', 'label': 'General',
            'columns': [
                [
                    {'name': 'arabic_name',  'label': 'Arabic Name',  'type': '1'},
                    {'name': 'subtitle',     'label': 'Subtitle',     'type': '1'},
                    {'name': 'period_from',  'label': 'Period From',  'type': '6',
                     'required': True, 'value': f'{current_year}-01-01'},
                    {'name': 'period_to',    'label': 'Period To',    'type': '6',
                     'required': True, 'value': f'{current_year}-12-31'},
                    {'name': 'crno',         'label': 'CR No',        'type': '1'},
                    {'name': 'licenseno',    'label': 'License No',   'type': '1'},
                    {'name': 'tinno',        'label': 'TIN No',       'type': '1'},
                ],
                [
                    {'name': 'phone',      'label': 'Phone',      'type': '14'},
                    {'name': 'mobile',     'label': 'Mobile',     'type': '14'},
                    {'name': 'email',      'label': 'Email',      'type': '13'},
                    {'name': 'website',    'label': 'Website',    'type': '1'},
                    # {'name': 'default_db', 'label': 'Default DB', 'type': '10',
                    #  'checkbox_label': 'Set as Default Database'},
                ],
            ],
        },
        {
            'id': 'address', 'label': 'Address',
            'columns': [
                [
                    {'name': 'address1',            'label': 'Address 1',  'type': '1'},
                    {'name': 'address2',            'label': 'Address 2',  'type': '1'},
                    {'name': 'address3',            'label': 'Address 3',  'type': '1'},
                    {'name': 'building_no',         'label': 'Building No','type': '1'},
                    {'name': 'street_name',         'label': 'Street Name','type': '1'},
                    {'name': 'plot_identification', 'label': 'Plot ID',    'type': '1'},
                ],
                [
                    {'name': 'zone',     'label': 'Zone',    'type': '1'},
                    {'name': 'area',     'label': 'Area',    'type': '1'},
                    {'name': 'city',     'label': 'City',    'type': '1'},
                    {'name': 'state',    'label': 'State',   'type': '1'},
                    {'name': 'district', 'label': 'District','type': '1'},
                    {'name': 'po_box',   'label': 'PO Box',  'type': '1'},
                ],
            ],
        },
        {
            'id': 'financial', 'label': 'Financial',
            'columns': [
                [
                    {'name': 'account_number', 'label': 'Account Number', 'type': '1'},
                    {'name': 'account_name',   'label': 'Account Name',   'type': '1'},
                    {'name': 'branch',         'label': 'Branch',         'type': '1'},
                    {'name': 'ifsc',           'label': 'IFSC',           'type': '1'},
                ],
                [
                    {'name': 'payer_id',   'label': 'Payer ID',   'type': '1'},
                    {'name': 'payer_bank', 'label': 'Payer Bank', 'type': '1'},
                    {'name': 'payer_iban', 'label': 'Payer IBAN', 'type': '1'},
                ],
            ],
        },
    ]

    return {
        'form_id'       : 'company-form',
        'form_name'     : 'Company_frm',
        'title'         : 'Company Information',
        'toolbar': [
            tb('Close',  'dfClose()',  danger=True),
            tb('Save',   'dfSave()'),
            tb('New',    'dfNew()'),
            tb('Delete', 'dfDelete()'),
        ],
        'menu_items': [
            # tb('Print',  'cfPrint()'),
            # {'sep': True, 'label': '', 'onclick': '', 'danger': False, 'icon': ''},
            tb('Design', "openFormDesign('company-form','Company_frm')"),
        ],
        'hero'          : None,
        'header_fields' : header_fields,
        'show_sidenav'  : False,
        'tabs'          : tabs,
    }


# ─── Page view ────────────────────────────────────────────────────────────────

@login_required
def company_form(request):
    business_type = request.session.get('business_type', 1)
    auto_select   = request.GET.get('select', '')

    try:
        customer_db = get_customer_db()
        companies   = (
            Organization.objects
            .using(customer_db)
            .values('CompanyId', 'CompanyName')
            .order_by('CompanyName')
        )
        company_options = [
            {'value': str(c['CompanyId']), 'label': c['CompanyName']}
            for c in companies
        ]

        if not auto_select:
            try:
                default_co = (
                    Organization.objects
                    .using(customer_db)
                    .filter(DefaultDb=1)
                    .values_list('CompanyId', flat=True)
                    .first()
                )
                if default_co:
                    auto_select = str(default_co)
            except Exception:
                pass

    except Exception as e:
        logger.error('company_form: failed to load companies: %s', e, exc_info=True)
        company_options = []

    config = _build_form_config(
        company_options=company_options,
        business_type=business_type,
    )
    return render(request, 'common/masters/company_form.html', {
        'form_config'         : config,
        'auto_select_company' : auto_select,
    })


# ─── CRUD endpoints ───────────────────────────────────────────────────────────

@require_http_methods(['GET'])
def lookup_company(request):
    return fetch_record_by_field_view(request, Organization, COMPANY_FIELD_MAPPING)


@require_http_methods(['GET'])
def search_company_by_name(request):
    return search_records_view(
        request, Organization, 'CompanyName', COMPANY_FIELD_MAPPING,
        display_fields=['company_code', 'company_name', 'city'],
    )


@require_http_methods(['POST'])
def save_company(request):
    """
    Update an existing company record only — creating new companies is blocked.

    After saving to customer_db, syncs the same data (best-effort) to:
      • company's provisioned DB  →  Organization + FirmMaster  (id = 1)
      • central registry DB       →  customers  (via softwares.db = DbName)
    """
    try:
        customer_db = get_customer_db()
        company_id  = request.POST.get('company_code')

        if not company_id:
            return JsonResponse({'success': False, 'error': 'Company code is required'})

        try:
            company_id_int = int(company_id)
        except (ValueError, TypeError):
            return JsonResponse(
                {'success': False, 'error': f'Invalid Company Code "{company_id}"'}
            )

        # ── Update-only guard ─────────────────────────────────────────────────
        try:
            company = Organization.objects.using(customer_db).get(
                CompanyId=company_id_int
            )
        except Organization.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error'  : (
                    f'Company "{company_id}" not found. '
                    'Creating new companies is not allowed here.'
                ),
            })

        # ── Apply POST values onto the instance ───────────────────────────────
        for form_field, db_field in FRONTEND_TO_DB_MAPPING.items():

            # System-managed — never accept from POST
            if db_field in ('DbName', 'CompanyId', 'DefaultDb'):
                continue

            value = request.POST.get(form_field)

            if db_field == 'BusinessType':
                bt = request.session.get('business_type', 1)
                try:
                    setattr(company, db_field, int(bt))
                except (ValueError, TypeError):
                    setattr(company, db_field, 1)

            elif db_field == 'DefaultDb':
                setattr(company, db_field, 1 if value in ('on', '1', True) else 0)

            elif db_field in ('PeriodFrom', 'PeriodTo'):
                if value:
                    try:
                        setattr(company, db_field,
                                datetime.strptime(value, '%Y-%m-%d').date())
                    except ValueError:
                        return JsonResponse(
                            {'success': False, 'error': f'Invalid date for {form_field}'}
                        )
                else:
                    yr = datetime.now().year
                    setattr(company, db_field,
                            datetime(yr, 1, 1).date()  if db_field == 'PeriodFrom'
                            else datetime(yr, 12, 31).date())

            else:
                setattr(company, db_field,
                        value.strip() if value and value.strip() else None)

        # ── Persist to customer_db ────────────────────────────────────────────
        company.save(using=customer_db)

        # ── Clear DefaultDb on all other companies if this one is default ─────
        # if getattr(company, 'DefaultDb', 0) == 1:
        #     (
        #         Organization.objects
        #         .using(customer_db)
        #         .exclude(CompanyId=company.CompanyId)
        #         .update(DefaultDb=0)
        #     )
        #     logger.info(
        #         'save_company: DefaultDb set on CompanyId=%s', company.CompanyId
        #     )

        logger.info('save_company: updated CompanyId=%s', company.CompanyId)

        # ── Sync downstream (best-effort, never fails the response) ───────────
        db_name = company.DbName
        _sync_provisioned_db(company, db_name)
        _sync_registry(company, db_name)

        return JsonResponse({
            'success'    : True,
            'message'    : 'Company updated successfully',
            'company_id' : company.CompanyId,
        })

    except Exception as e:
        logger.error('save_company: %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(['GET'])
def get_company(request, company_id):
    try:
        company = get_object_or_404(
            Organization.objects.using(get_customer_db()), CompanyId=company_id
        )
        data = {}
        for db_field, form_field in COMPANY_FIELD_MAPPING.items():
            value = getattr(company, db_field, None)
            if value is None:
                data[form_field] = None
            elif hasattr(value, 'strftime'):
                data[form_field] = value.strftime('%Y-%m-%d')
            elif db_field == 'DefaultDb':
                data[form_field] = value == 1 if isinstance(value, int) else bool(value)
            else:
                data[form_field] = str(value)
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        logger.error('get_company: %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(['POST'])
def delete_company(request, company_id):
    """
    Deletes the Organization record from customer_db.
    The provisioned PostgreSQL database is NOT dropped automatically.
    """
    try:
        customer_db = get_customer_db()
        company     = get_object_or_404(
            Organization.objects.using(customer_db), CompanyId=company_id
        )
        name    = company.CompanyName
        db_name = company.DbName
        company.delete(using=customer_db)

        return JsonResponse({
            'success': True,
            'message': f'Company "{name}" deleted',
            'note'   : (
                f'The associated database "{db_name}" was NOT dropped. '
                'Delete it manually via pgAdmin or psql if no longer needed.'
            ) if db_name else None,
        })
    except Exception as e:
        logger.error('delete_company: %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})