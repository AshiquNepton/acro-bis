# common/views/ftp_browse.py
"""
GET /common/ftp/browse/?path=documents/logos
Returns folder listing for the current company's FTP directory.

Security
--------
- Login required.
- `path` is sandwiched between FTP_ROOT/common/{company_folder}/ and
  never allowed to escape it (.. and absolute paths are rejected).
- Only image + PDF extensions are returned in the files list.
"""

import ftplib
import logging
import os

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from common.views.decorators import login_required
from core.ftp import FTPManager, _ftp_root, _sanitise
from typing import Optional

logger = logging.getLogger(__name__)

_ALLOWED_EXT = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.pdf'}
_IMAGE_EXT   = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}


def _safe_relative(path: str) -> Optional[str]:
    """
    Normalise a caller-supplied relative path.
    Returns None if the path tries to escape (contains .. or is absolute).
    """
    if not path:
        return ''
    # Reject absolute paths and traversal attempts
    norm = os.path.normpath(path).replace('\\', '/')
    if norm.startswith('/') or norm.startswith('..') or '/..' in norm:
        return None
    # Strip leading ./ artefact from normpath
    if norm == '.':
        return ''
    return norm


@require_GET
@login_required
def ftp_browse(request):
    """
    Query params
    ------------
    path  : relative sub-path inside the company folder  (default: '')
            e.g. ''  → lists documents/ and employees/ at company root
                 'documents/logos' → lists that subfolder

    Response
    --------
    {
        "base":    "/erp/common/NEPTUNE_BUSINESS_SYSTEM_2",
        "path":    "documents/logos",
        "folders": ["subfolder1", ...],
        "files":   [{"name": "logo.png", "path": "documents/logos/logo.png",
                     "type": "image"}, ...]
    }
    """
    company_folder = request.session.get('company_folder', '')
    if not company_folder:
        return JsonResponse({'error': 'No company in session'}, status=400)

    rel_path = _safe_relative(request.GET.get('path', ''))
    if rel_path is None:
        return JsonResponse({'error': 'Invalid path'}, status=400)

    # Build the absolute remote directory to list
    base_dir    = f'{_ftp_root()}/common/{_sanitise(company_folder)}'
    remote_dir  = f'{base_dir}/{rel_path}'.rstrip('/')

    try:
        ftp = FTPManager()
        folders, files = _list_entries(ftp, remote_dir)
    except Exception as e:
        logger.warning('[ftp_browse] %s', e)
        return JsonResponse({'error': str(e)}, status=502)

    # Filter files to allowed extensions only
    allowed_files = []
    for name in files:
        ext = os.path.splitext(name)[1].lower()
        if ext in _ALLOWED_EXT:
            file_rel = f'{rel_path}/{name}'.lstrip('/')
            allowed_files.append({
                'name': name,
                'path': file_rel,
                'type': 'image' if ext in _IMAGE_EXT else 'pdf',
            })

    return JsonResponse({
        'base':    base_dir,
        'path':    rel_path,
        'folders': sorted(folders),
        'files':   allowed_files,
    })


def _list_entries(ftp_mgr: FTPManager, remote_dir: str):
    """
    Returns (folders: list[str], files: list[str]).
    Tries MLSD first (modern servers); falls back to NLST + heuristic.
    """
    folders, files = [], []

    with ftp_mgr._connect() as ftp:
        # Try MLSD (RFC 3659) — gives us type=dir / type=file facts
        try:
            for name, facts in ftp.mlsd(remote_dir):
                if name in ('.', '..'):
                    continue
                entry_type = facts.get('type', '').lower()
                if entry_type == 'dir':
                    folders.append(name)
                elif entry_type == 'file':
                    files.append(name)
            return folders, files

        except ftplib.error_perm:
            pass  # MLSD not supported — fall through to NLST

        # NLST fallback — heuristic: entry has an extension → file, else → folder
        try:
            entries = ftp.nlst(remote_dir)
        except ftplib.error_perm:
            return [], []   # empty or non-existent directory

        for entry in entries:
            name = entry.split('/')[-1]
            if name in ('.', '..') or not name:
                continue
            if '.' in name:
                files.append(name)
            else:
                folders.append(name)

    return folders, files