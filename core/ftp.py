# core/ftp.py
"""
FTP Manager
===========
Credentials are read from .env (via Django settings).

Folder structure on FTP server:
    {FTP_ROOT}/
    └── {module}/                          e.g.  laundry / restaurant / inventory …
        └── {company_code}/                e.g.  C001
            ├── documents/                 shared company-level folder
            └── employees/
                └── {employee_code}/       e.g.  E0042

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUICK USAGE IN ANY VIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    from core.ftp import FTPManager

    ftp = FTPManager()

    # Upload all browse_btn files from request.FILES in one call.
    # Returns dict {form_field: remote_path} for fields that uploaded OK.
    # NON-BLOCKING — never raises, always returns (even on FTP failure).
    uploaded = ftp.upload_from_request(
        request,
        module        = 'inventory',
        company_code  = request.session.get('company_code'),
        employee_code = item_code,             # omit for company-level
        fields        = {                      # form_field → FTP filename (or None = use original name)
            'item_image'  : None,
            'item_document': None,
        },
    )

    # Merge paths back into POST data before passing to BaseCRUD.save()
    post_data = request.POST.copy()
    post_data.update(uploaded)
    return crud.save(post_data)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OTHER OPERATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ftp.check_connection()          # prints status, returns bool
    ftp.upload_file(local_path, module, company_code, employee_code)
    ftp.upload_bytes(data, filename, module, company_code, employee_code)
    ftp.download_file(filename, module, company_code, employee_code)
    ftp.delete_file(filename, module, company_code, employee_code)
    ftp.list_files(module, company_code, employee_code)
    ftp.ensure_folder(module, company_code, employee_code)
"""

import ftplib
import io
import logging
import os
import socket
import tempfile
from contextlib import contextmanager
from django.conf import settings

logger = logging.getLogger(__name__)

MODULES = {'laundry', 'restaurant', 'inventory', 'financial', 'common'}


# ─── Lazy credential accessors ────────────────────────────────────────────────
# Read from Django settings at CALL TIME, not at import time.
# This guarantees .env values are always loaded before we read them,
# and prevents stale defaults (e.g. 'ftp.yourserver.com') from being
# captured at startup before django-environ / python-dotenv has run.

def _get_setting(key: str, default: str = '') -> str:
    return str(getattr(settings, key, os.environ.get(key, default))).strip()


def _ftp_host()     -> str: return _get_setting('FTP_HOST')
def _ftp_port()     -> int: return int(_get_setting('FTP_PORT', '21') or 21)
def _ftp_user()     -> str: return _get_setting('FTP_USER')
def _ftp_password() -> str: return _get_setting('FTP_PASSWORD')
def _ftp_root()     -> str: return _get_setting('FTP_ROOT', '/erp').rstrip('/')


def ftp_configured() -> bool:
    """Return True if all required FTP credentials are present in .env."""
    return bool(_ftp_host() and _ftp_user() and _ftp_password())


# ─── Helpers ─────────────────────────────────────────────────────────────────



def _sanitise(value: str) -> str:
    return str(value).strip().replace('/', '_').replace('\\', '_').replace('..', '')


def _build_path(module: str,
                company_code: str,
                employee_code: str = None,
                group_code: str = None,
                company_name: str = None) -> str:
    """
    Build the remote directory path.

    Structure:
      Company-level : {root}/{module}/{company_name}_{company_code}/documents/[{group_code}/]
      Employee-level: {root}/{module}/{company_name}_{company_code}/employees/{employee_code}/[{group_code}/]

    Examples:
      /erp/inventory/NEPTUNE_BUSINESS_SYSTEM_2/items/20/photo.jpg
      /erp/financial/NEPTUNE_BUSINESS_SYSTEM_2/documents/44/invoice.pdf
    """
    root = _ftp_root()
    m    = _sanitise(module)
    c    = _sanitise(company_code)

    # Build company folder: sanitised_name_id or just id if no name given
    if company_name:
        safe = company_name.upper().strip()
        safe = ''.join(ch if ch.isalnum() else '_' for ch in safe)
        safe = '_'.join(filter(None, safe.split('_')))
        company_dir = f'{safe}_{c}'
    else:
        company_dir = c

    if employee_code:
        base = f'{root}/{m}/{company_dir}/employees/{_sanitise(employee_code)}'
    else:
        base = f'{root}/{m}/{company_dir}/documents'

    if group_code:
        base = f'{base}/{_sanitise(str(group_code))}'

    return base


def _mkdir_p(ftp: ftplib.FTP, remote_dir: str) -> None:
    """Recursively create directories on the FTP server (mkdir -p behaviour)."""
    parts = [p for p in remote_dir.split('/') if p]
    current = ''
    for part in parts:
        current += '/' + part
        try:
            ftp.mkd(current)
        except ftplib.error_perm as e:
            if not str(e).startswith('550'):   # 550 = already exists, safe to ignore
                raise


def _log(symbol: str, message: str) -> None:
    """Print a formatted FTP status line inside the save progress block."""
    print(f'│  {symbol}  FTP {message}')


# ─── FTPManager ──────────────────────────────────────────────────────────────

class FTPManager:
    """
    Thread-safe FTP helper. Opens a fresh connection per operation.
    All public methods print status to the VS Code terminal.
    """

    def __init__(self, host=None, port=None, user=None, password=None, root=None):
        # Read credentials lazily so .env is always fully loaded first
        self.host     = host     or _ftp_host()
        self.port     = int(port or _ftp_port())
        self.user     = user     or _ftp_user()
        self.password = password or _ftp_password()
        self.root     = (root    or _ftp_root()).rstrip('/')

    # ── Connection check ──────────────────────────────────────────────────

    def check_connection(self, silent: bool = False) -> bool:
        """
        Test connectivity + credentials. Prints result to terminal.

        Returns True on success, False on any failure.
        Pass silent=True to suppress terminal output.

        Terminal examples:
          │  ✔  FTP Connected → ftp.server.com:21  (user: ftpuser)
          │  ✗  FTP Not configured — set FTP_HOST, FTP_USER, FTP_PASSWORD in .env
          │  ✗  FTP Connection timed out → ftp.server.com:21 — timed out
          │  ✗  FTP Login failed → ftp.server.com:21 — 530 Login incorrect
        """
        if not ftp_configured():
            if not silent:
                _log('✗', 'Not configured — set FTP_HOST, FTP_USER, FTP_PASSWORD in .env')
            return False

        ftp = ftplib.FTP()
        try:
            ftp.connect(self.host, self.port, timeout=10)
        except (socket.timeout, OSError, ftplib.all_errors) as e:
            if not silent:
                _log('✗', f'Connection timed out → {self.host}:{self.port} — {e}')
            logger.warning('[FTP] check_connection failed: %s', e)
            return False

        try:
            ftp.login(self.user, self.password)
        except ftplib.error_perm as e:
            if not silent:
                _log('✗', f'Login failed → {self.host}:{self.port} — {e}')
            logger.warning('[FTP] login failed: %s', e)
            try:
                ftp.quit()
            except Exception:
                pass
            return False

        welcome = ''
        try:
            welcome = ftp.getwelcome() or ''
            ftp.quit()
        except Exception:
            pass

        if not silent:
            _log('✔', f'Connected → {self.host}:{self.port}  (user: {self.user})')
            if welcome:
                _log('ℹ', f'Server: {welcome.strip()[:80]}')
        return True

    # ── Internal connect context-manager ──────────────────────────────────

    @contextmanager
    def _connect(self):
        """Yield an authenticated ftplib.FTP. Prints status to terminal."""
        if not ftp_configured():
            _log('✗', 'Not configured — set FTP_HOST, FTP_USER, FTP_PASSWORD in .env')
            raise ConnectionError('FTP credentials not configured')

        ftp = ftplib.FTP()
        try:
            ftp.connect(self.host, self.port, timeout=30)
            ftp.login(self.user, self.password)
            ftp.set_pasv(True)
            _log('✔', f'Connected → {self.host}:{self.port}')
            logger.debug('[FTP] Connected to %s:%s', self.host, self.port)
            yield ftp
        except ftplib.error_perm as e:
            _log('✗', f'Login failed → {self.host}:{self.port} — {e}')
            logger.error('[FTP] Login error: %s', e, exc_info=True)
            raise
        except (socket.timeout, OSError) as e:
            _log('✗', f'Connection timed out → {self.host}:{self.port} — {e}')
            logger.error('[FTP] Timeout: %s', e)
            raise
        except ftplib.all_errors as e:
            _log('✗', f'Error → {self.host}:{self.port} — {e}')
            logger.error('[FTP] Error: %s', e, exc_info=True)
            raise
        finally:
            try:
                ftp.quit()
            except Exception:
                pass

    # ── ★ UNIVERSAL REQUEST UPLOAD ────────────────────────────────────────

    def upload_from_request(
        self,
        request,
        module: str,
        company_code: str,
        fields: dict,
        employee_code: str = None,
        group_code: str = None,
    ) -> dict:
        """
        Upload all browse_btn files present in request.FILES.

        Parameters
        ----------
        request       : Django HttpRequest
        module        : FTP module folder  e.g. 'hrms'
        company_code  = request.session.get('company_code'),
        fields        : dict mapping form_field_name → remote_filename override (or None)
                        e.g. {'hr_document': None, 'hired_from_doc': None}
                        Files are expected in request.FILES as {field}_file
        employee_code : optional — if given, files go into employees/{code}/ subfolder

        Returns
        -------
        dict  {form_field: remote_path}  for every field that uploaded successfully.
              Fields that failed or had no file are omitted (non-blocking).

        NON-BLOCKING — catches all errors. Never raises.
        DB save always continues regardless of FTP outcome.

        Terminal output:
          │  ✔  FTP [hr_document] → /erp/hrms/C001/employees/100/contract.pdf
          │  ⚠  FTP [hired_from_doc] skipped — timed out
          │  ⚠  FTP skipping — not configured in .env
        """
        uploaded = {}

        # Filter to only the fields that actually have a file in this request
        pending = {
            field: request.FILES[field + '_file']
            for field in fields
            if field + '_file' in request.FILES
        }

        if not pending:
            return uploaded

        if not ftp_configured():
            _log('⚠', f'Skipping upload — FTP not configured in .env '
                       f'({", ".join(pending.keys())})')
            return uploaded

        for field_name, uploaded_file in pending.items():
            remote_filename = fields.get(field_name) or uploaded_file.name
            suffix   = os.path.splitext(uploaded_file.name)[1] or '.bin'
            tmp_path = None

            try:
                # Write Django InMemoryUploadedFile to a real temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    for chunk in uploaded_file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                with open(tmp_path, 'rb') as f:
                    data = f.read()

                remote_path = self.upload_bytes(
                    data          = data,
                    filename      = remote_filename,
                    module        = module,
                    company_code  = company_code,
                    employee_code = employee_code,
                    group_code    = group_code,
                )
                uploaded[field_name] = remote_path
                print(f'│')
                print(f'│  ✔  FTP Document Saved')
                print(f'│     Field    : {field_name}')
                print(f'│     File     : {uploaded_file.name}')
                print(f'│     Size     : {len(data):,} bytes')
                print(f'│     Server   : {self.host}:{self.port}')
                print(f'│     Path     : {remote_path}')
                print(f'│')

            except Exception as e:
                logger.warning('[FTP] upload_from_request: %s skipped: %s', field_name, e)
                _log('⚠', f'[{field_name}] skipped (DB save continues) — {e}')
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass

        return uploaded

    # ── Folder operations ─────────────────────────────────────────────────

    def ensure_folder(self, module: str, company_code: str,
                      employee_code: str = None,
                      company_name: str = None) -> str:
        if module not in MODULES:
            raise ValueError(f'Unknown module "{module}". Allowed: {MODULES}')
        remote_dir = _build_path(module, company_code, employee_code,
                                 company_name=company_name)
        with self._connect() as ftp:
            _mkdir_p(ftp, remote_dir)
        _log('✔', f'Folder ready: {remote_dir}')
        return remote_dir

    def list_files(self, module: str, company_code: str,
                   employee_code: str = None,
                   company_name: str = None) -> list:
        remote_dir = _build_path(module, company_code, employee_code,
                                 company_name=company_name)
        try:
            with self._connect() as ftp:
                _mkdir_p(ftp, remote_dir)
                ftp.cwd(remote_dir)
                names = ftp.nlst()
            _log('✔', f'Listed {len(names)} file(s) in {remote_dir}')
            return names
        except ftplib.error_perm as e:
            _log('✗', f'list_files error: {e}')
            return []

    def upload_file(self, local_path: str, module: str, company_code: str,
                    remote_filename: str = None,
                    employee_code: str = None,
                    company_name: str = None) -> str:
        if not os.path.isfile(local_path):
            raise FileNotFoundError(f'Local file not found: {local_path}')
        remote_dir  = _build_path(module, company_code, employee_code,
                                  company_name=company_name)
        remote_name = remote_filename or os.path.basename(local_path)
        remote_path = f'{remote_dir}/{remote_name}'
        with self._connect() as ftp:
            _mkdir_p(ftp, remote_dir)
            with open(local_path, 'rb') as f:
                ftp.storbinary(f'STOR {remote_path}', f)
        _log('✔', f'Uploaded: {remote_path}')
        return remote_path

    def upload_bytes(self, data: bytes, filename: str, module: str,
                     company_code: str,
                     employee_code: str = None,
                     group_code: str = None,
                     company_name: str = None) -> str:
        remote_dir  = _build_path(module, company_code, employee_code,
                                  group_code, company_name=company_name)
        remote_path = f'{remote_dir}/{_sanitise(filename)}'
        with self._connect() as ftp:
            _mkdir_p(ftp, remote_dir)
            ftp.storbinary(f'STOR {remote_path}', io.BytesIO(data))
        _log('✔', f'Uploaded: {remote_path} ({len(data):,} bytes)')
        return remote_path

    def download_file(self, remote_filename: str, module: str,
                      company_code: str,
                      employee_code: str = None,
                      company_name: str = None) -> bytes:
        remote_dir  = _build_path(module, company_code, employee_code,
                                  company_name=company_name)
        remote_path = f'{remote_dir}/{_sanitise(remote_filename)}'
        buf = io.BytesIO()
        try:
            with self._connect() as ftp:
                ftp.retrbinary(f'RETR {remote_path}', buf.write)
        except ftplib.error_perm as e:
            if '550' in str(e):
                raise FileNotFoundError(f'Remote file not found: {remote_path}')
            raise
        buf.seek(0)
        return buf.read()

    def delete_file(self, remote_filename: str, module: str,
                    company_code: str,
                    employee_code: str = None,
                    company_name: str = None) -> bool:
        remote_dir  = _build_path(module, company_code, employee_code,
                                  company_name=company_name)
        remote_path = f'{remote_dir}/{_sanitise(remote_filename)}'
        try:
            with self._connect() as ftp:
                ftp.delete(remote_path)
            _log('✔', f'Deleted: {remote_path}')
            return True
        except ftplib.error_perm as e:
            if '550' in str(e):
                _log('⚠', f'Delete: not found — {remote_path}')
                return False
            raise

    def file_exists(self, remote_filename: str, module: str,
                    company_code: str,
                    employee_code: str = None,
                    company_name: str = None) -> bool:
        remote_dir  = _build_path(module, company_code, employee_code,
                                  company_name=company_name)
        remote_path = f'{remote_dir}/{_sanitise(remote_filename)}'
        try:
            with self._connect() as ftp:
                ftp.size(remote_path)
            return True
        except ftplib.error_perm:
            return False


# ─── Module-scoped subclasses ─────────────────────────────────────────────────
# Each sets MODULE so you don't have to pass module= every time.

class LaundryFTP(FTPManager):
    MODULE = 'laundry'

    def upload(self, local_path, company_code, remote_filename=None, employee_code=None):
        return self.upload_file(local_path, self.MODULE, company_code,
                                remote_filename=remote_filename, employee_code=employee_code)

    def upload_raw(self, data, filename, company_code, employee_code=None):
        return self.upload_bytes(data, filename, self.MODULE, company_code, employee_code)

    def upload_request(self, request, company_code, fields, employee_code=None):
        return self.upload_from_request(request, self.MODULE, company_code,
                                        fields, employee_code)

    def download(self, filename, company_code, employee_code=None):
        return self.download_file(filename, self.MODULE, company_code, employee_code)


class RestaurantFTP(FTPManager):
    MODULE = 'restaurant'

    def upload(self, local_path, company_code, remote_filename=None, employee_code=None):
        return self.upload_file(local_path, self.MODULE, company_code,
                                remote_filename=remote_filename, employee_code=employee_code)

    def upload_raw(self, data, filename, company_code, employee_code=None):
        return self.upload_bytes(data, filename, self.MODULE, company_code, employee_code)

    def upload_request(self, request, company_code, fields, employee_code=None):
        return self.upload_from_request(request, self.MODULE, company_code,
                                        fields, employee_code)

    def download(self, filename, company_code, employee_code=None):
        return self.download_file(filename, self.MODULE, company_code, employee_code)





class InventoryFTP(FTPManager):
    MODULE = 'inventory'

    def upload(self, local_path, company_code, remote_filename=None, employee_code=None):
        return self.upload_file(local_path, self.MODULE, company_code,
                                remote_filename=remote_filename, employee_code=employee_code)

    def upload_raw(self, data, filename, company_code, employee_code=None):
        return self.upload_bytes(data, filename, self.MODULE, company_code, employee_code)

    def upload_request(self, request, company_code, fields, employee_code=None):
        return self.upload_from_request(request, self.MODULE, company_code,
                                        fields, employee_code)


class FinancialFTP(FTPManager):
    MODULE = 'financial'

    def upload(self, local_path, company_code, remote_filename=None, employee_code=None):
        return self.upload_file(local_path, self.MODULE, company_code,
                                remote_filename=remote_filename, employee_code=employee_code)

    def upload_raw(self, data, filename, company_code, employee_code=None):
        return self.upload_bytes(data, filename, self.MODULE, company_code, employee_code)

    def upload_request(self, request, company_code, fields, employee_code=None):
        return self.upload_from_request(request, self.MODULE, company_code,
                                        fields, employee_code)