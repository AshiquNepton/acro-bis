# common/views/global_settings.py
"""
Global Settings — config view + Settings & Image (Logo) Management
===================================================================

ALL persistence is via ChartOfCode (category='OrgOptions').

  Images  → code='IMAGEPATH'   type_code=<image_key>   description=<ftp_path>
  Fields  → code=<field_name>  type_code='value'        description=<value>

Endpoints
─────────
  gs_config          GET  — returns the _gsConfig data island (modal schema)
  gs_load_settings   GET  — load all settings-tab field values from ChartOfCode
  gs_save_settings   POST — save all settings-tab field values to ChartOfCode
  gs_load_images     GET  — load current FTP paths from ChartOfCode
  gs_upload_image    POST — upload via FTP, persist path in ChartOfCode
  gs_delete_image    POST — delete from FTP, clear ChartOfCode path
  gs_serve_image     GET  — proxy image bytes from FTP to browser (no auth)

Register in common/urls.py:
    from common.views.global_settings import (
        gs_config,
        gs_load_settings, gs_save_settings,
        gs_load_images, gs_upload_image,
        gs_delete_image, gs_serve_image,
    )

    path('gs/config/',            gs_config,          name='gs_config'),
    path('gs/settings/load/',     gs_load_settings,   name='gs_load_settings'),
    path('gs/settings/save/',     gs_save_settings,   name='gs_save_settings'),
    path('gs/images/load/',       gs_load_images,     name='gs_load_images'),
    path('gs/images/upload/',     gs_upload_image,    name='gs_upload_image'),
    path('gs/images/delete/',     gs_delete_image,    name='gs_delete_image'),
    path('gs/images/serve/',      gs_serve_image,     name='gs_serve_image'),
"""

import io
import json as _json
import logging
import mimetypes

from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_http_methods

from core.ftp import FTPManager, ftp_configured, _sanitise, _ftp_root, _mkdir_p
from common.middleware.database_middleware import get_customer_db
from common.models.chart_of_code import ChartOfCode
from common.views.decorators import login_required


logger = logging.getLogger(__name__)

# ── ChartOfCode constants ──────────────────────────────────────────────────────

COC_CATEGORY = 'OrgOptions'   # shared category for all global-settings rows
COC_IMG_CODE = 'IMAGEPATH'    # code for every image-path row
COC_FIELD_TC = 'value'        # fixed type_code used for every settings field

# ── Image slot keys ────────────────────────────────────────────────────────────

IMAGE_TYPES = {
    'header_full_logo': 'Header Full Logo',
    'header_side_logo': 'Header Side Logo',
    'footer_full_logo': 'Footer Full Logo',
    'footer_side_logo': 'Footer Side Logo',
}

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}

_MIME_MAP = {
    '.jpg':  'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png':  'image/png',
    '.gif':  'image/gif',
    '.webp': 'image/webp',
    '.svg':  'image/svg+xml',
    '.bmp':  'image/bmp',
}

# ── FTP directory helpers ──────────────────────────────────────────────────────

SOFTWARE_MODULE = {1: 'laundry', 2: 'restaurant'}
DEFAULT_MODULE  = 'common'


def _get_session_company(request):
    return (
        request.session.get('company_code'),
        request.session.get('company_name', ''),
        request.session.get('software_id'),
    )


def _build_company_dir(company_code, company_name):
    if company_name:
        safe = company_name.upper().strip()
        safe = ''.join(ch if ch.isalnum() else '_' for ch in safe)
        safe = '_'.join(filter(None, safe.split('_')))
        return f'{safe}_{_sanitise(str(company_code))}'
    return _sanitise(str(company_code))


def _image_remote_dir(company_code, company_name, image_type, software_id=None):
    root        = _ftp_root()
    module      = SOFTWARE_MODULE.get(int(software_id or 0), DEFAULT_MODULE)
    company_dir = _build_company_dir(company_code, company_name)
    return f'{root}/{module}/{company_dir}/images/{_sanitise(image_type)}'


def _mime_for(filename):
    ext = ('.' + filename.rsplit('.', 1)[-1].lower()) if '.' in filename else ''
    return _MIME_MAP.get(ext) or mimetypes.guess_type(filename)[0] or 'application/octet-stream', ext


def _fmt_size(b):
    if b < 1024:    return f'{b} B'
    if b < 1048576: return f'{b / 1024:.1f} KB'
    return f'{b / 1048576:.2f} MB'


def _is_safe_image_path(path):
    return '/images/' in path


# ── Config builder ─────────────────────────────────────────────────────────────

def _build_gs_config():
    """
    Return the Python dict that drives the Global Settings modal.
    Shape mirrors what global_settings_modal.js expects in window._gsConfig.
 
    Field 'name' values are used directly as ChartOfCode 'code':
        Category = 'OrgOptions'
        Code     = <field.name>   e.g. 'amount_prefix', 'decimals', 'employee_report_logo'
        TypeCode = 'value'
        Description = <saved value>
    """
    # Build image-slot options list dynamically from IMAGE_TYPES so the
    # dropdown always matches whatever slots are defined above.
    image_options = [{'value': '', 'label': '— None —'}] + [
        {'value': key, 'label': label}
        for key, label in IMAGE_TYPES.items()
    ]
 
    return {
        'title':    'Global Settings',
        'subtitle': '',
        'tabs': [
            {
                'id':    'settings',
                'label': '» Settings',
                'icon':  'Settings',
                'fields': [
                    {
                        'name':        'amount_prefix',
                        'label':       'Amount Prefix',
                        'type':        'text',
                        'value':       '',
                        'placeholder': 'e.g. QR, $, AED',
                        'maxlength':   10,
                    },
                    {
                        'name':  'decimals',
                        'label': 'Decimals',
                        'type':  'number',
                        'value': '2',
                        'min':   0,
                        'max':   6,
                        'step':  1,
                    },
                    # ── NEW FIELD ──────────────────────────────────────────
                    # Saved as: Category=OrgOptions  Code=employee_report_logo
                    #           TypeCode=value        Description=<image_key>
                    {
                        'name':    'employee_report_logo',
                        'label':   'Employee Report Logo',
                        'type':    'select',
                        'value':   '',          # default: none
                        'options': image_options,
                    },
                    # ── END NEW FIELD ──────────────────────────────────────
                ],
            },
            {
                'id':    'images',
                'label': '» Images',
                'icon':  'Upload',
                'type':  'images',
                'slots': [
                    {
                        'key':   'header_full_logo',
                        'label': 'Header Full Logo',
                        'hint':  'Full-width logo — shown on the login page and expanded sidebar header.',
                    },
                    {
                        'key':   'header_side_logo',
                        'label': 'Header Side Logo',
                        'hint':  'Compact logo — shown in the collapsed sidebar header.',
                    },
                    {
                        'key':   'footer_full_logo',
                        'label': 'Footer Full Logo',
                        'hint':  'Full logo displayed in the page footer.',
                    },
                    {
                        'key':   'footer_side_logo',
                        'label': 'Footer Side Logo',
                        'hint':  'Compact logo displayed in the page footer.',
                    },
                ],
            },
        ],
    }

# ── Config endpoint ────────────────────────────────────────────────────────────

@require_http_methods(['GET'])
@login_required
def gs_config(request):
    """Return the modal config as JSON for the template data island."""
    return JsonResponse({'success': True, 'config': _build_gs_config()})


# ── ChartOfCode helpers ────────────────────────────────────────────────────────

def _coc_get_image(db_alias, image_type):
    """Read a single image FTP path from ChartOfCode. Returns '' if not set."""
    return ChartOfCode.get(
        db_alias,
        category  = COC_CATEGORY,
        code      = COC_IMG_CODE,
        type_code = image_type,
    ) or ''


def _coc_set_image(db_alias, image_type, ftp_path):
    """Write (upsert) an image FTP path into ChartOfCode."""
    ChartOfCode.set(
        db_alias,
        category    = COC_CATEGORY,
        code        = COC_IMG_CODE,
        type_code   = image_type,
        description = ftp_path or '',
    )


def _coc_read_all_images(db_alias):
    """Return {image_type: ftp_path} for all known image slots."""
    rows = ChartOfCode.load(
        db_alias,
        category = COC_CATEGORY,
        code     = COC_IMG_CODE,
    )
    return {k: rows.get(k, '') for k in IMAGE_TYPES}


def _coc_get_field(db_alias, field_name):
    """
    Read a single settings-field value from ChartOfCode.
    Stored as: Category=OrgOptions  Code=<field_name>  TypeCode='value'
    """
    return ChartOfCode.get(
        db_alias,
        category  = COC_CATEGORY,
        code      = field_name,
        type_code = COC_FIELD_TC,
    )


def _coc_set_field(db_alias, field_name, value):
    """
    Write (upsert) a settings-field value into ChartOfCode.
    Stored as: Category=OrgOptions  Code=<field_name>  TypeCode='value'
    """
    ChartOfCode.set(
        db_alias,
        category    = COC_CATEGORY,
        code        = field_name,
        type_code   = COC_FIELD_TC,
        description = str(value),
    )


def _settings_field_names():
    """Return list of field 'name' values declared in the settings tab."""
    cfg = _build_gs_config()
    for tab in cfg.get('tabs', []):
        if tab.get('id') == 'settings':
            return [f['name'] for f in tab.get('fields', [])]
    return []


# ── Settings endpoints ─────────────────────────────────────────────────────────

@require_http_methods(['GET'])
@login_required
def gs_load_settings(request):
    """
    Load all settings-tab field values from ChartOfCode.

    ChartOfCode layout per field:
        Category    = 'OrgOptions'
        Code        = <field_name>   e.g. 'amount_prefix'
        TypeCode    = 'value'
        Description = <stored value>

    Response:
        { success: true, settings: { amount_prefix: 'QR', decimals: '2', … } }

    Fields not yet saved return the default value declared in _build_gs_config().
    """
    db = get_customer_db()

    # Build defaults from config so JS always gets a complete object
    cfg      = _build_gs_config()
    defaults = {}
    for tab in cfg.get('tabs', []):
        if tab.get('id') == 'settings':
            for f in tab.get('fields', []):
                defaults[f['name']] = str(f.get('value', ''))

    settings = {}
    for field_name, default in defaults.items():
        stored = _coc_get_field(db, field_name)
        settings[field_name] = stored if stored is not None else default

    return JsonResponse({'success': True, 'settings': settings})


@require_http_methods(['POST'])
@login_required
def gs_save_settings(request):
    """
    Save all settings-tab field values to ChartOfCode.

    ChartOfCode layout per field:
        Category    = 'OrgOptions'
        Code        = <field_name>   e.g. 'amount_prefix'
        TypeCode    = 'value'
        Description = <posted value>

    Expects POST keys matching field 'name' values in the settings tab.
    Unknown keys are silently ignored.

    Response:
        { success: true, saved: ['amount_prefix', 'decimals'] }
    """
    db          = get_customer_db()
    field_names = _settings_field_names()
    saved       = []
    errors      = []

    for field_name in field_names:
        if field_name in request.POST:
            value = request.POST[field_name].strip()
            try:
                _coc_set_field(db, field_name, value)
                saved.append(field_name)
            except Exception as e:
                logger.error(
                    '[gs_save_settings] field=%s error=%s', field_name, e, exc_info=True
                )
                errors.append(field_name)

    if errors:
        return JsonResponse({
            'success': False,
            'error':   f'Could not save: {", ".join(errors)}',
            'saved':   saved,
        })

    return JsonResponse({'success': True, 'saved': saved})


# ── Image endpoints ────────────────────────────────────────────────────────────

@require_http_methods(['GET'])
@login_required
def gs_load_images(request):
    """
    Load current image FTP paths from ChartOfCode.

    ChartOfCode layout per image:
        Category    = 'OrgOptions'
        Code        = 'IMAGEPATH'
        TypeCode    = <image_key>   e.g. 'header_full_logo'
        Description = <ftp_path>

    Response:
        {
          success: true,
          images:     { header_full_logo: '/ftp/path/…', … },
          serve_urls: { header_full_logo: '/common/gs/images/serve/?path=…', … },
        }
    """
    db     = get_customer_db()
    images = _coc_read_all_images(db)

    serve_urls = {
        img_type: (f'/common/gs/images/serve/?path={ftp_path}' if ftp_path else '')
        for img_type, ftp_path in images.items()
    }

    return JsonResponse({'success': True, 'images': images, 'serve_urls': serve_urls})


@require_http_methods(['POST'])
@login_required
def gs_upload_image(request):
    """
    Upload an image via FTP and persist its path in ChartOfCode.

    POST fields:
        image_type  — one of IMAGE_TYPES keys
        image_file  — the image file

    ChartOfCode layout:
        Category    = 'OrgOptions'
        Code        = 'IMAGEPATH'
        TypeCode    = <image_type>
        Description = <remote_ftp_path>
    """
    image_type = request.POST.get('image_type', '').strip()

    if image_type not in IMAGE_TYPES:
        return JsonResponse({
            'success': False,
            'error':   f'Invalid image_type "{image_type}". Allowed: {", ".join(IMAGE_TYPES)}',
        })

    if 'image_file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file provided (field: image_file)'})

    file_obj = request.FILES['image_file']
    filename = file_obj.name
    _, ext   = _mime_for(filename)

    if ext not in ALLOWED_EXTENSIONS:
        return JsonResponse({
            'success': False,
            'error':   f'File type "{ext}" not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}',
        })

    company_code, company_name, software_id = _get_session_company(request)
    if not company_code:
        return JsonResponse({'success': False, 'error': 'Session expired — please login again.'})

    if not ftp_configured():
        return JsonResponse({'success': False, 'error': 'FTP not configured — set FTP_HOST/USER/PASSWORD in .env'})

    try:
        data        = b''.join(file_obj.chunks())
        remote_dir  = _image_remote_dir(company_code, company_name, image_type, software_id)
        remote_path = f'{remote_dir}/{_sanitise(filename)}'

        ftp = FTPManager()
        with ftp._connect() as f:
            _mkdir_p(f, remote_dir)
            f.storbinary(f'STOR {remote_path}', io.BytesIO(data))

        logger.info('[gs_upload_image] %s → %s (%s bytes)', image_type, remote_path, len(data))

    except Exception as e:
        logger.error('[gs_upload_image] FTP error: %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': f'Upload failed: {e}'})

    try:
        db = get_customer_db()
        _coc_set_image(db, image_type, remote_path)
    except Exception as e:
        logger.error('[gs_upload_image] ChartOfCode write error: %s', e, exc_info=True)
        return JsonResponse({
            'success':  False,
            'error':    f'File uploaded but could not save path: {e}',
            'ftp_path': remote_path,
        })

    return JsonResponse({
        'success':    True,
        'message':    'Image uploaded successfully',
        'image_type': image_type,
        'ftp_path':   remote_path,
        'serve_url':  f'/common/gs/images/serve/?path={remote_path}',
        'filename':   filename,
        'size':       _fmt_size(len(data)),
    })


@require_http_methods(['POST'])
@login_required
def gs_delete_image(request):
    """
    Delete an image from FTP and clear its ChartOfCode path.

    POST fields:
        image_type  — one of IMAGE_TYPES keys
    """
    image_type = request.POST.get('image_type', '').strip()

    if image_type not in IMAGE_TYPES:
        return JsonResponse({'success': False, 'error': f'Invalid image_type "{image_type}"'})

    company_code, company_name, software_id = _get_session_company(request)
    if not company_code:
        return JsonResponse({'success': False, 'error': 'Session expired — please login again.'})

    db       = get_customer_db()
    ftp_path = _coc_get_image(db, image_type)

    if ftp_path and ftp_configured():
        try:
            ftp = FTPManager()
            with ftp._connect() as f:
                f.delete(ftp_path)
        except Exception as e:
            logger.warning('[gs_delete_image] FTP delete skipped (%s): %s', ftp_path, e)

    try:
        _coc_set_image(db, image_type, '')
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Could not clear path: {e}'})

    return JsonResponse({'success': True, 'message': 'Image removed', 'image_type': image_type})


@require_http_methods(['GET'])
def gs_serve_image(request):
    """
    Proxy logo images from FTP.
    No @login_required — needed for public header/footer rendering.
    Only paths containing /images/ are served (guards against FTP proxy abuse).
    """
    ftp_path = request.GET.get('path', '').strip()
    if not ftp_path:
        raise Http404('path parameter is required')

    if '..' in ftp_path or not _is_safe_image_path(ftp_path):
        raise Http404('Invalid path')

    if not ftp_configured():
        raise Http404('FTP not configured')

    try:
        filename       = ftp_path.split('/')[-1]
        mime_type, ext = _mime_for(filename)

        if ext not in ALLOWED_EXTENSIONS:
            raise Http404('File type not allowed')

        buf = io.BytesIO()
        ftp = FTPManager()
        with ftp._connect() as f:
            f.retrbinary(f'RETR {ftp_path}', buf.write)
        buf.seek(0)
        data = buf.read()

        response = HttpResponse(data, content_type=mime_type)
        response['Content-Disposition']    = f'inline; filename="{filename}"'
        response['Content-Length']         = len(data)
        response['Cache-Control']          = 'public, max-age=3600'
        response['X-Content-Type-Options'] = 'nosniff'
        return response

    except Http404:
        raise
    except Exception as e:
        logger.error('[gs_serve_image] %s', e, exc_info=True)
        raise Http404(f'Image not found: {e}')


# ── Context processor helper ───────────────────────────────────────────────────

def gs_context(request):
    """
    Returns a dict to be merged into every page context so base.html can
    render the data island:

        <script>window._gsConfig = {{ gs_config_json|safe }};</script>

    Add to a context_processor or call directly from any view.
    """
    return {'gs_config_json': _json.dumps(_build_gs_config())}