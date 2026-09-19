"""
common/views/form_design.py   v2.1

FIXES vs v2.0:
  1. DUPLICATE KEY — replaced SELECT+INSERT/UPDATE pattern with a single
     atomic INSERT … ON CONFLICT DO UPDATE (upsert). Eliminates the race
     condition where two concurrent saves (e.g. fdToggleEnabled + Save All)
     both saw "not exists" and both tried to INSERT the same PK.

  2. Removed nested function _int_or_none (defined inside a loop) —
     moved to module level to avoid repeated redefinition.

  3. Minor: consolidated duplicate `import json` / `from django.http import JsonResponse`.
"""
import json
import logging

from django.http       import JsonResponse
from django.db         import connections
from core.crud         import safe_atomic

logger = logging.getLogger(__name__)

# ── DDL ───────────────────────────────────────────────────────────────────────
CREATE_SQL = """
CREATE TABLE IF NOT EXISTS "FormDesign" (
    "ForamName"     VARCHAR(50)  NOT NULL,
    "TypeCode"      INTEGER      NOT NULL DEFAULT 0,
    "ControlName"   VARCHAR(60)  NOT NULL,
    "Left"          INTEGER,
    "Top"           INTEGER,
    "Width"         INTEGER,
    "Height"        INTEGER,
    "Row"           INTEGER      DEFAULT 1,
    "Container"     VARCHAR(50),
    "TabIndex"      INTEGER,
    "TabStop"       SMALLINT,
    "Visible"       SMALLINT     DEFAULT 1,
    "Caption"       VARCHAR(100),
    "Value"         INTEGER,
    "Design"        SMALLINT     DEFAULT 0,
    "Enabled"       SMALLINT     DEFAULT 1,
    "ArabicCaption" VARCHAR(60),
    "Font"          VARCHAR(60),
    "FontSize"      INTEGER,
    PRIMARY KEY ("ForamName", "TypeCode", "ControlName")
)
"""

ALTER_SQLS = [
    'ALTER TABLE "FormDesign" ALTER COLUMN "ControlName"   TYPE VARCHAR(60)',
    'ALTER TABLE "FormDesign" ALTER COLUMN "ForamName"     TYPE VARCHAR(50)',
    'ALTER TABLE "FormDesign" ALTER COLUMN "Caption"       TYPE VARCHAR(100)',
    'ALTER TABLE "FormDesign" ALTER COLUMN "ArabicCaption" TYPE VARCHAR(60)',
    'ALTER TABLE "FormDesign" ALTER COLUMN "Font"          TYPE VARCHAR(60)',
    'ALTER TABLE "FormDesign" ALTER COLUMN "Container"     TYPE VARCHAR(50)',
    'ALTER TABLE "FormDesign" ADD COLUMN IF NOT EXISTS "Row" INTEGER DEFAULT 1',
]

# ── UPSERT SQL (single atomic statement — no race condition) ──────────────────
UPSERT_SQL = """
INSERT INTO "FormDesign"
    ("ForamName", "TypeCode", "ControlName",
     "Left", "Top", "Width", "Height", "Row",
     "TabIndex", "TabStop", "Visible", "Caption",
     "Design", "Enabled", "ArabicCaption", "Font", "FontSize")
VALUES
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT ("ForamName", "TypeCode", "ControlName")
DO UPDATE SET
    "Left"          = EXCLUDED."Left",
    "Top"           = EXCLUDED."Top",
    "Width"         = EXCLUDED."Width",
    "Height"        = EXCLUDED."Height",
    "Row"           = EXCLUDED."Row",
    "TabIndex"      = EXCLUDED."TabIndex",
    "TabStop"       = EXCLUDED."TabStop",
    "Visible"       = EXCLUDED."Visible",
    "Caption"       = EXCLUDED."Caption",
    "Design"        = EXCLUDED."Design",
    "Enabled"       = EXCLUDED."Enabled",
    "ArabicCaption" = EXCLUDED."ArabicCaption",
    "Font"          = EXCLUDED."Font",
    "FontSize"      = EXCLUDED."FontSize"
"""


def _db(request):
    return 'customer_db'


_ENSURED_FORM_DESIGN_TABLES = set()


def _ensure_table(cursor, db_alias='customer_db', force=False):
    if not force and db_alias in _ENSURED_FORM_DESIGN_TABLES:
        return
    cursor.execute(CREATE_SQL)
    for sql in ALTER_SQLS:
        try:
            cursor.execute(sql)
        except Exception:
            pass
    _ENSURED_FORM_DESIGN_TABLES.add(db_alias)


def _int_or_none(v):
    """Convert a value to int, or None if blank/invalid."""
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


# ── LOAD ──────────────────────────────────────────────────────────────────────
def load_form_design(request):
    form_name = request.GET.get('form', '')
    if not form_name:
        return JsonResponse({'success': False, 'error': 'form param required'})
    try:
        db_alias = _db(request)
        with connections[db_alias].cursor() as cur:
            _ensure_table(cur, db_alias)
            cur.execute(
                'SELECT "ControlName","TypeCode","Left","Top","Width","Height","Row",'
                '"TabIndex","TabStop","Visible","Caption","Design","Enabled",'
                '"ArabicCaption","Font","FontSize" '
                'FROM "FormDesign" WHERE "ForamName" = %s ORDER BY "TabIndex"',
                [form_name]
            )
            rows = cur.fetchall()
        controls = [
            {
                'controlName'  : r[0],
                'typeCode'     : r[1],
                'left'         : r[2],
                'top'          : r[3],
                'width'        : r[4],   # INTEGER: 8000 = 80%, 200 = 200px
                'height'       : r[5],
                'row'          : r[6] if r[6] is not None else 1,
                'tabIndex'     : r[7],
                'tabStop'      : r[8],
                'visible'      : r[9],
                'caption'      : r[10],
                'design'       : r[11],
                'enabled'      : r[12],
                'arabicCaption': r[13],
                'font'         : r[14],
                'fontSize'     : r[15],
            }
            for r in rows
        ]
        return JsonResponse({'success': True, 'controls': controls})
    except Exception as e:
        logger.error('load_form_design error: %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


# ── SAVE ──────────────────────────────────────────────────────────────────────
def save_form_design(request):
    if request.method != 'POST':
        return JsonResponse({'success': False})
    try:
        data      = json.loads(request.body)
        form_name = str(data.get('form', ''))[:50]
        controls  = data.get('controls', [])
        if not form_name:
            return JsonResponse({'success': False, 'error': 'form required'})

        db_alias = _db(request)
        with safe_atomic(db_alias):
            with connections[db_alias].cursor() as cur:
                _ensure_table(cur, db_alias)
                saved = 0
                for c in controls:
                    ctrl_name = str(c.get('controlName', ''))[:60]
                    if not ctrl_name:
                        continue

                    type_code  = int(c.get('typeCode', 0))
                    width_val  = _int_or_none(c.get('width'))
                    height_val = _int_or_none(c.get('height'))
                    row_val    = _int_or_none(c.get('row')) or 1

                    cur.execute(UPSERT_SQL, [
                        form_name,
                        type_code,
                        ctrl_name,
                        c.get('left'),
                        c.get('top'),
                        width_val,
                        height_val,
                        row_val,
                        c.get('tabIndex'),
                        int(c.get('tabStop', 1)),
                        int(c.get('visible', 1)),
                        str(c.get('caption', '') or '')[:100],
                        int(c.get('design', 1)),
                        int(c.get('enabled', 1)),
                        str(c.get('arabicCaption', '') or '')[:60],
                        str(c.get('font', '') or '')[:60],
                        c.get('fontSize'),
                    ])
                    saved += 1

        return JsonResponse({'success': True, 'message': f'Saved {saved} controls'})
    except Exception as e:
        logger.error('save_form_design error: %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


# ── RESET ─────────────────────────────────────────────────────────────────────
def reset_form_design(request):
    if request.method != 'POST':
        return JsonResponse({'success': False})
    try:
        data      = json.loads(request.body)
        form_name = str(data.get('form', ''))[:50]
        if not form_name:
            return JsonResponse({'success': False})
        with connections[_db(request)].cursor() as cur:
            cur.execute('DELETE FROM "FormDesign" WHERE "ForamName"=%s', [form_name])
        return JsonResponse({'success': True, 'message': 'Design reset to defaults'})
    except Exception as e:
        logger.error('reset_form_design error: %s', e, exc_info=True)
        return JsonResponse({'success': False})


# ── DELETE (single control) ───────────────────────────────────────────────────
def form_design_delete(request):
    if request.method != 'POST':
        return JsonResponse({'success': False})
    try:
        data         = json.loads(request.body)
        form_name    = str(data.get('form',        '')).strip()[:50]
        control_name = str(data.get('controlName', '')).strip()[:60]
        if not form_name or not control_name:
            return JsonResponse({'success': False, 'error': 'Missing form or controlName'})
        with connections[_db(request)].cursor() as cur:
            cur.execute(
                'DELETE FROM "FormDesign" '
                'WHERE "ForamName"=%s AND "TypeCode"=0 AND "ControlName"=%s',
                [form_name, control_name]
            )
            deleted = cur.rowcount
        return JsonResponse({'success': True, 'deleted': deleted})
    except Exception as e:
        logger.error('form_design_delete error: %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})
    

    