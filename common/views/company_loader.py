# common/views/company_loader.py
import logging
from django.db import connections
from django.db.utils import OperationalError, ProgrammingError

logger = logging.getLogger(__name__)


def load_company_to_session(request) -> bool:
    """
    Query the Organization table on customer_db and store key fields
    in the session so every view and template has them without re-querying.

    Called once right after successful login (before redirect to home).

    Session keys written
    ────────────────────
      company_id       int
      company_code     str   ← used by all FTP calls
      company_name     str
      company_arabic   str | None
      company_subtitle str | None
      period_from      str  "YYYY-MM-DD"
      period_to        str  "YYYY-MM-DD"
      business_type    int
      company_tin      str | None
      company_cr       str | None

    Returns True on success, False if the table is unreachable.
    Never raises.
    """
    try:
        # ── Manually push credentials into customer_db ────────────────────────
        # DynamicDatabaseMiddleware already ran at the START of this request,
        # before the login view wrote the new DB credentials to the session.
        # So customer_db is still pointing at the default local socket.
        # We must reconfigure it here using the credentials now in the session.
        db_host     = request.session.get('db_host')
        db_port     = request.session.get('db_port', '5432')
        db_name     = request.session.get('db_name')
        db_user     = request.session.get('db_user')
        db_password = request.session.get('db_password')

        if not all([db_host, db_name, db_user, db_password]):
            logger.warning('[company_loader] DB credentials not in session yet.')
            print('|  [WARN] Company load skipped -- DB credentials missing from session')
            return False

        # Reconfigure the thread-local credentials and close stale connection
        from common.db_backend.base import set_db_credentials
        set_db_credentials(db_host, db_port, db_name, db_user, db_password)
        try:
            connections['customer_db'].close()
        except Exception:
            pass

        print(f'|  [INFO] Company loader using: {db_host}/{db_name}')

        # ── Query Organization ────────────────────────────────────────────────
        with connections['customer_db'].cursor() as cursor:
            cursor.execute("""
                SELECT
                    "CompanyId",
                    "CompanyName",
                    "ArabicName",
                    "Subtitle",
                    "PeriodFrom",
                    "PeriodTo",
                    "BusinessType",
                    "TinNo",
                    "CrNo"
                FROM "Organization"
                WHERE "DefaultDb" = 1
                LIMIT 1
            """)
            row = cursor.fetchone()

        if not row:
            # Fallback — if no default is set, take the first company
            logger.warning('[company_loader] No DefaultDb=1 found, falling back to first company.')
            print('|  [WARN] No default company set -- loading first available company')
            with connections['customer_db'].cursor() as cursor:
                cursor.execute("""
                    SELECT
                        "CompanyId",
                        "CompanyName",
                        "ArabicName",
                        "Subtitle",
                        "PeriodFrom",
                        "PeriodTo",
                        "BusinessType",
                        "TinNo",
                        "CrNo"
                    FROM "Organization"
                    ORDER BY "CompanyId"
                    LIMIT 1
                """)
                row = cursor.fetchone()

        if not row:
            logger.warning('[company_loader] Organization table is empty.')
            print('|  [WARN] Company load skipped -- Organization table is empty')
            return False

        (company_id, name, arabic, subtitle,
         period_from, period_to, biz_type, tin, cr) = row

        # ── Build sanitised FTP folder name: CompanyName_CompanyId ───────────
        # e.g. "NEPTUNE BUSINESS SYSTEM" + 2 → "NEPTUNE_BUSINESS_SYSTEM_2"
        safe_name = (name or 'company').upper().strip()
        safe_name = ''.join(c if c.isalnum() else '_' for c in safe_name)
        safe_name = '_'.join(filter(None, safe_name.split('_')))  # collapse multiple underscores
        company_folder = f'{safe_name}_{company_id}'             # e.g. NEPTUNE_BUSINESS_SYSTEM_2

        # ── Write to session ──────────────────────────────────────────────────
        request.session['company_id']       = company_id
        request.session['company_code']     = str(company_id)
        request.session['company_folder']   = company_folder     # ← NEW — used by FTP path
        request.session['company_name']     = name or ''
        request.session['company_arabic']   = arabic or ''
        request.session['company_subtitle'] = subtitle or ''
        request.session['period_from']      = str(period_from) if period_from else ''
        request.session['period_to']        = str(period_to)   if period_to   else ''
        request.session['business_type']    = biz_type
        request.session['company_tin']      = tin or ''
        request.session['company_cr']       = cr  or ''
        request.session.modified = True

        print(f'|  [OK] Company loaded -> [{company_id}] {name}  '
              f'({period_from} - {period_to})')
        print(f'|     FTP folder : {company_folder}')
        logger.info('[company_loader] Loaded company %s (%s) folder=%s',
                    company_id, name, company_folder)
        return True

    except (OperationalError, ProgrammingError) as e:
        logger.error('[company_loader] DB error: %s', e)
        print(f'|  [WARN] Company load skipped -- DB not ready: {e}')
        return False
    except Exception as e:
        logger.error('[company_loader] Unexpected error: %s', e, exc_info=True)
        print(f'|  [WARN] Company load failed: {e}')
        return False