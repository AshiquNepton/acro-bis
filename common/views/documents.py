# common/views/documents.py
"""
Universal Document endpoints — FTP only, no database table.

Files are stored on FTP under:
    /erp/{module}/{company_name}_{company_code}/{ref_id}/{group_id}/filename

Three endpoints:
    load_docs   GET  ?module=hrms&ref_id=E001&group_id=44
                     → lists files in that FTP folder
    save_doc    POST module, ref_id, group_id, doc_file
                     → uploads file to FTP, returns path
    delete_doc  POST path
                     → deletes file from FTP
    serve_doc   GET  ?path=/erp/hrms/...
                     → proxies file from FTP to browser

Register in common/urls.py:
    from common.views.documents import load_docs, save_doc, delete_doc, serve_doc

    path('docs/load/',   load_docs,  name='load_docs'),
    path('docs/save/',   save_doc,   name='save_doc'),
    path('docs/delete/', delete_doc, name='delete_doc'),
    path('docs/serve/',  serve_doc,  name='serve_doc'),
"""

import io
import logging
import mimetypes
import os

from core.utils import _fmt_size
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_http_methods

from core.ftp import FTPManager, ftp_configured, _build_path
from common.middleware.database_middleware import get_customer_db

logger = logging.getLogger(__name__)


# ── MIME helpers ──────────────────────────────────────────────────────────────

_MIME_MAP = {
    '.pdf' : 'application/pdf',
    '.doc' : 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xls' : 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.ppt' : 'application/vnd.ms-powerpoint',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.jpg' : 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png' : 'image/png',
    '.gif' : 'image/gif',
    '.webp': 'image/webp',
    '.bmp' : 'image/bmp',
    '.txt' : 'text/plain',
    '.csv' : 'text/csv',
    '.zip' : 'application/zip',
    '.rar' : 'application/x-rar-compressed',
    '.mp4' : 'video/mp4',
    '.mp3' : 'audio/mpeg',
}

_INLINE = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.txt', '.mp4', '.mp3'}


def _mime(filename):
    ext = ('.' + filename.rsplit('.', 1)[-1].lower()) if '.' in filename else ''
    return _MIME_MAP.get(ext) or mimetypes.guess_type(filename)[0] or 'application/octet-stream', ext


def _get_group_label(db_alias, group_id):
    """Fetch group label from ItemGroups safely."""
    if not group_id:
        return ''
    try:
        from django.db import connections
        with connections[db_alias].cursor() as cur:
            cur.execute(
                'SELECT "Description" FROM "ItemGroups" WHERE "GroupID" = %s',
                [group_id]
            )
            row = cur.fetchone()
            return row[0] if row else str(group_id)
    except Exception:
        return str(group_id)


def _get_company_from_session(request):
    """
    Returns (company_code, company_name) from session.
    Returns (None, None) if session is missing required keys.
    """
    company_code = request.session.get('company_code')
    company_name = request.session.get('company_name', '')
    return company_code, company_name


# ── Endpoints ─────────────────────────────────────────────────────────────────

@require_http_methods(['GET'])
def load_docs(request):
    """
    List files in the FTP folder for module/ref_id/group_id.
    GET ?module=hrms&ref_id=E001&group_id=44

    If group_id is omitted, lists all files across all group subfolders.
    Returns list of {doc, file_path, size, group_id} rows.
    """
    module   = request.GET.get('module',   '').strip()
    ref_id   = request.GET.get('ref_id',   '').strip()
    group_id = request.GET.get('group_id', '').strip() or None

    if not module or not ref_id:
        return JsonResponse({'success': False, 'rows': [],
                             'error': 'module and ref_id are required'})

    if not ftp_configured():
        return JsonResponse({'success': True, 'rows': [],
                             'warning': 'FTP not configured'})

    company_code, company_name = _get_company_from_session(request)
    if not company_code:
        return JsonResponse({'success': False, 'rows': [],
                             'error': 'Session expired — please login again.'})

    db = get_customer_db()

    try:
        ftp  = FTPManager()
        rows = []

        if group_id:
            # List one specific group folder
            remote_dir = _build_path(module, company_code,
                                     employee_code=ref_id,
                                     group_code=group_id,
                                     company_name=company_name)
            files = _list_folder(ftp, remote_dir)
            for fname, fsize in files:
                rows.append({
                    'doc'        : fname,
                    'file_path'  : remote_dir + '/' + fname,
                    'size'       : fsize,
                    'group_id'   : group_id,
                    'group_label': _get_group_label(db, group_id),
                    'date'       : '',
                })
        else:
            # List all group subfolders under ref_id
            base_dir = _build_path(module, company_code,
                                   employee_code=ref_id,
                                   company_name=company_name)
            subfolders = _list_subfolders(ftp, base_dir)
            for gid in subfolders:
                sub_dir = base_dir + '/' + gid
                files   = _list_folder(ftp, sub_dir)
                for fname, fsize in files:
                    rows.append({
                        'doc'        : fname,
                        'file_path'  : sub_dir + '/' + fname,
                        'size'       : fsize,
                        'group_id'   : gid,
                        'group_label': _get_group_label(db, gid),
                        'date'       : '',
                    })

        return JsonResponse({'success': True, 'rows': rows})

    except Exception as e:
        logger.error('[load_docs] %s', e, exc_info=True)
        return JsonResponse({'success': True, 'rows': [],
                             'warning': f'Could not list files: {e}'})


def _list_folder(ftp_mgr, remote_dir):
    """Returns [(filename, size_str)] for files in remote_dir. Empty list on error."""
    try:
        results = []
        with ftp_mgr._connect() as f:
            try:
                f.cwd(remote_dir)
            except Exception:
                return []
            try:
                for name, facts in f.mlsd():
                    if facts.get('type') == 'file':
                        size = int(facts.get('size', 0))
                        results.append((name, _fmt_size(size)))
            except Exception:
                names = f.nlst()
                for name in names:
                    if name not in ('.', '..'):
                        results.append((name, ''))
        return results
    except Exception:
        return []


def _list_subfolders(ftp_mgr, remote_dir):
    """Returns list of subfolder names under remote_dir."""
    try:
        folders = []
        with ftp_mgr._connect() as f:
            try:
                f.cwd(remote_dir)
            except Exception:
                return []
            try:
                for name, facts in f.mlsd():
                    if facts.get('type') == 'dir':
                        folders.append(name)
            except Exception:
                pass
        return folders
    except Exception:
        return []




@require_http_methods(['POST'])
def save_doc(request):
    """
    Upload a file to FTP.
    POST: module, ref_id, group_id (required), doc_file (file)
    Returns {success, file_path, doc, message}
    """
    module   = request.POST.get('module',   '').strip()
    ref_id   = request.POST.get('ref_id',   '').strip()
    group_id = request.POST.get('group_id', '').strip()

    if not module or not ref_id:
        return JsonResponse({'success': False,
                             'error': 'module and ref_id are required'})

    if not group_id:
        return JsonResponse({'success': False,
                             'error': 'Group is required — please select a group'})

    if 'doc_file' not in request.FILES:
        return JsonResponse({'success': False,
                             'error': 'No file provided'})

    if not ftp_configured():
        return JsonResponse({'success': False,
                             'error': 'FTP not configured — set FTP_HOST/USER/PASSWORD in .env'})

    company_code, company_name = _get_company_from_session(request)
    if not company_code:
        return JsonResponse({'success': False,
                             'error': 'Session expired — please login again.'})

    file_obj = request.FILES['doc_file']
    filename = file_obj.name

    print(f'|')
    print(f'|  -> FTP Upload starting...')
    print(f'|     Module   : {module}')
    print(f'|     Company  : {company_name} ({company_code})')
    print(f'|     Ref ID   : {ref_id}')
    print(f'|     Group    : {group_id}')
    print(f'|     File     : {filename}')

    try:
        data = b''.join(file_obj.chunks())

        ftp = FTPManager()
        remote_path = ftp.upload_bytes(
            data         = data,
            filename     = filename,
            module       = module,
            company_code = company_code,
            company_name = company_name,
            employee_code= ref_id,
            group_code   = group_id,
        )

        print(f'|  [OK]  Upload complete')
        print(f'|     Size     : {len(data):,} bytes')
        print(f'|     Path     : {remote_path}')
        print(f'|')

        return JsonResponse({
            'success'  : True,
            'message'  : 'File uploaded',
            'doc'      : filename,
            'file_path': remote_path,
            'size'     : _fmt_size(len(data)),
        })

    except Exception as e:
        logger.error('[save_doc] %s', e, exc_info=True)
        print(f'|  [ERROR]  Upload failed: {e}')
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(['POST'])
def delete_doc(request):
    """
    Delete a file from FTP.
    POST: path (full remote path)
    """
    file_path = request.POST.get('path', '').strip()
    if not file_path:
        return JsonResponse({'success': False, 'error': 'path is required'})

    if not ftp_configured():
        return JsonResponse({'success': False, 'error': 'FTP not configured'})

    try:
        ftp = FTPManager()
        with ftp._connect() as f:
            f.delete(file_path)
        print(f'|  [OK]  FTP Deleted: {file_path}')
        return JsonResponse({'success': True, 'message': 'File deleted'})
    except Exception as e:
        logger.error('[delete_doc] %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(['GET'])
def serve_doc(request):
    """
    Proxy any file from FTP to the browser.
    GET ?path=/erp/hrms/NEPTUNE_BUSINESS_SYSTEM_2/employees/20/photo.jpg

    PDF, images → inline in browser
    Word, Excel, ZIP etc. → download with correct filename
    """
    file_path = request.GET.get('path', '').strip()
    if not file_path:
        raise Http404('path is required')

    if not ftp_configured():
        raise Http404('FTP not configured')

    try:
        filename       = file_path.split('/')[-1]
        mime_type, ext = _mime(filename)
        disposition    = 'inline' if ext in _INLINE else 'attachment'

        print(f'|  -> Serving: {file_path}')
        buf = io.BytesIO()
        ftp = FTPManager()
        with ftp._connect() as f:
            f.retrbinary('RETR ' + file_path, buf.write)
        buf.seek(0)
        data = buf.read()
        print(f'|  [OK]  Served: {filename} ({len(data):,} bytes)')

        response = HttpResponse(data, content_type=mime_type)
        response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
        response['Content-Length']      = len(data)
        response['X-Content-Type-Options'] = 'nosniff'
        return response

    except Exception as e:
        logger.error('[serve_doc] %s', e, exc_info=True)
        raise Http404(f'File not found: {e}')