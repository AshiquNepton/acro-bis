# common/views/group_setup.py
import json
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import connections
from common.theme_constants import tb
from common.views.decorators import login_required


logger = logging.getLogger(__name__)


def _db(request):
    return 'customer_db'


ITEM_GROUP_CATEGORIES = [
    {'id': '1',   'label': 'Item Group'},
    {'id': '2',   'label': 'Item Category'},
    {'id': '3',   'label': 'Item Company'},
    {'id': '4',   'label': 'Item Brand'},
    {'id': '5',   'label': 'Details'},
    {'id': '6',   'label': 'Measure'},
    {'id': '7',   'label': 'Tax Group'},
    {'id': '8',   'label': 'Stock Group'},
    {'id': '9',   'label': 'Item Unit'},
    {'id': '10',  'label': 'State'},
    {'id': '13',  'label': 'Designation'},
    {'id': '16',  'label': 'Warehouse'},
    {'id': '27',  'label': 'Employee Type'},
    {'id': '29',  'label': 'Group 1'},
    {'id': '30',  'label': 'Group 2'},
    {'id': '31',  'label': 'Group 3'},
    {'id': '201', 'label': 'Group 4'},
    {'id': '202', 'label': 'Group 5'},
    {'id': '44',  'label': 'Actual Job'},
    {'id': '51',  'label': 'Nationality'},
    {'id': '52',  'label': 'Religion'},
    {'id': '53',  'label': 'Bank Name'},
    {'id': '68',  'label': 'Status'},
    {'id': '69',  'label': 'Blood Group'},
    {'id': '97',  'label': 'Qualification'},
    {'id': '98',  'label': 'Accommodation'},
    {'id': '99',  'label': 'Experience'},
    {'id': '100', 'label': 'Passport With'},
    {'id': '101', 'label': 'Ticket Duration'},
    {'id': '102', 'label': 'Off Day'},
    {'id': '129', 'label': 'Packing'},
    {'id': '130', 'label': 'Department'},
    {'id': '131', 'label': 'Section'},
    {'id': '132', 'label': 'Family'},
    {'id': '133', 'label': 'Flavour'},
    {'id': '134', 'label': 'Color'},
    {'id': '135', 'label': 'Sex'},
    {'id': '136', 'label': 'Document Group'},
    {'id': '138', 'label': 'Country Of Origin'},
    {'id': '144', 'label': 'Leave Type'},
    {'id': '145', 'label': 'Application Type'},
]


def _build_form_config():
    return {
        'form_id': 'group-setup',
        'toolbar': [
            tb('Close',  'dfClose()',  danger=True),
            tb('Save',   'dfSave()'),
            tb('Delete', 'dfDelete()'),
        ],
        'menu_items': [
            tb('Change', 'gsChange()'),
            tb('Print',  'window.print()'),
        ],
        'hero':          None,
        'header_fields': None,
        'tabs':          None,
        'show_sidenav':  False,
    }

@login_required
def group_setup(request):
    """Standalone — no sidebar."""
    context = {
        'categories'    : ITEM_GROUP_CATEGORIES,
        'fc'            : _build_form_config(),
        'base_template' : 'common/base.html',
        'page_title'    : 'Group Setup',
    }
    return render(request, 'common/masters/group_setup.html', context)


# ── CRUD endpoints (shared by all apps) ──────────────────────────────────────

def group_setup_load(request):
    cat_id = request.GET.get('category', '').strip()
    try:
        typecode = int(cat_id)
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'rows': []})
    try:
        with connections[_db(request)].cursor() as cur:
            cur.execute(
                'SELECT "GroupID","Description","UCode" FROM "ItemGroups" '
                'WHERE "Category"=%s ORDER BY "GroupID"',
                [typecode]
            )
            rows = [{'id': r[0], 'description': r[1] or '', 'code': r[2] or ''} for r in cur.fetchall()]
        return JsonResponse({'success': True, 'rows': rows})
    except Exception as e:
        logger.error('group_setup_load: %s', e, exc_info=True)
        return JsonResponse({'success': False, 'rows': []})


def group_setup_save(request):
    if request.method != 'POST':
        return JsonResponse({'success': False})
    try:
        data      = json.loads(request.body)
        typecode  = int(data.get('category', 0))
        to_save   = data.get('to_save',   [])
        to_delete = data.get('to_delete', [])

        db_alias = _db(request)
        from django.db import transaction
        with transaction.atomic(using=db_alias):
            with connections[db_alias].cursor() as cur:
                # Exclusive lock prevents concurrency race conditions during MAX() calculation
                cur.execute('LOCK TABLE "ItemGroups" IN EXCLUSIVE MODE')

                for gid in to_delete:
                    cur.execute('DELETE FROM "ItemGroups" WHERE "GroupID"=%s', [int(gid)])

                cur.execute('SELECT COALESCE(MAX("GroupID"), 0) FROM "ItemGroups"')
                next_id = cur.fetchone()[0] + 1

                for row in to_save:
                    desc = (row.get('description') or '').strip()
                    code = (row.get('code') or '').strip() or None
                    gid  = row.get('id')
                    if not desc:
                        continue
                    if gid:
                        # existing row — update
                        cur.execute(
                            'UPDATE "ItemGroups" SET "Description"=%s,"UCode"=%s '
                            'WHERE "GroupID"=%s',
                            [desc, code, int(gid)]
                        )
                    else:
                        # new row
                        cur.execute(
                            'INSERT INTO "ItemGroups" '
                            '("GroupID","Category","Description","UCode","Under","NREC") '
                            'VALUES (%s,%s,%s,%s,%s,%s)',
                            [next_id, typecode, desc, code, 1, None]
                        )
                        next_id += 1

                # Return updated rows immediately to avoid an extra load round trip
                cur.execute(
                    'SELECT "GroupID","Description","UCode" FROM "ItemGroups" '
                    'WHERE "Category"=%s ORDER BY "GroupID"',
                    [typecode]
                )
                rows = [{'id': r[0], 'description': r[1] or '', 'code': r[2] or ''} for r in cur.fetchall()]

        return JsonResponse({'success': True, 'rows': rows})
    except Exception as e:
        logger.error('group_setup_save: %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


def group_setup_delete(request):
    if request.method != 'POST':
        return JsonResponse({'success': False})
    try:
        data = json.loads(request.body)
        gid  = int(data.get('id', 0))
        with connections[_db(request)].cursor() as cur:
            cur.execute('DELETE FROM "ItemGroups" WHERE "GroupID"=%s', [gid])
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error('group_setup_delete: %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})