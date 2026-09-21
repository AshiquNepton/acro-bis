"""
common/services/party_service.py

Reusable business operations for the Customer / Vendor (Party) domain.

All raw-SQL CRUD against ChartOfAccounts + CustomerVendor lives here so that
any vertical (laundry, restaurant, inventory …) can call these functions
without duplicating logic.

Tables
──────
  ChartOfAccounts  — master account record
  CustomerVendor   — extended contact / financial details

Usage
─────
    from common.services.party_service import save_party, load_party

    # In a customer view:
    save_party(request, mgroup=CUSTOMER_MGROUP)

    # In a vendor view:
    save_party(request, mgroup=VENDOR_MGROUP)
"""

import json
import logging

from django.db import connections, transaction
from django.http import JsonResponse

from common.models.customer import (
    CHART_OF_ACCOUNTS_DDL,
    CUSTOMER_VENDOR_DDL,
    CUSTOMER_VENDOR_FIELDS,
)

logger = logging.getLogger(__name__)

# ── DB alias helper ──────────────────────────────────────────────────────────

def _get_db(request) -> str:
    """Return the tenant DB alias for this request."""
    return 'customer_db'


# ── Table bootstrap ──────────────────────────────────────────────────────────

_ENSURED_PARTY_DBS: set = set()


def ensure_party_tables(db_alias: str) -> None:
    """
    Create ChartOfAccounts and CustomerVendor tables if they don't exist.
    Cached per process so the check runs at most once per DB alias.
    """
    if db_alias in _ENSURED_PARTY_DBS:
        return

    try:
        with connections[db_alias].cursor() as cur:
            # Use the DDL constants from the model — single source of truth
            cur.execute(CHART_OF_ACCOUNTS_DDL)
            cur.execute(CUSTOMER_VENDOR_DDL)
        _ENSURED_PARTY_DBS.add(db_alias)
    except Exception as e:
        logger.error('ensure_party_tables(%s): %s', db_alias, e)


# ── CRUD operations ──────────────────────────────────────────────────────────

def save_party(request, mgroup: int) -> JsonResponse:
    """
    Create or update a party (customer or vendor) record.

    Reads JSON body from request; uses mgroup to distinguish party type
    (CUSTOMER_MGROUP=36, VENDOR_MGROUP=37).
    """
    try:
        data = json.loads(request.body)
        ac_code = data.get('AcCode')
        if not ac_code:
            return JsonResponse({'success': False, 'error': 'Account Code is required'})

        description = data.get('Description')
        if not description:
            return JsonResponse({'success': False, 'error': 'Account Name is required'})

        active = 1 if data.get('Active') else 0
        group_id = int(data.get('GroupID', 1) or 1)

        db_alias = _get_db(request)
        ensure_party_tables(db_alias)

        with transaction.atomic(using=db_alias):
            with connections[db_alias].cursor() as cur:
                # Check existence
                cur.execute(
                    'SELECT "AccountID" FROM "ChartOfAccounts" WHERE "AcCode" = %s AND "MGroup" = %s',
                    [ac_code, mgroup],
                )
                row = cur.fetchone()

                if row:
                    # ── UPDATE ────────────────────────────────────────────
                    account_id = row[0]
                    cur.execute(
                        '''
                        UPDATE "ChartOfAccounts"
                        SET "Description"=%s, "ArabicDesc"=%s, "GroupID"=%s,
                            "Active"=%s, "Address1"=%s
                        WHERE "AccountID"=%s
                        ''',
                        [description, data.get('ArabicDesc'), group_id,
                         active, data.get('Address1'), account_id],
                    )

                    set_clause = ', '.join([f'"{f}" = %s' for f in CUSTOMER_VENDOR_FIELDS])
                    params = [data.get(f) for f in CUSTOMER_VENDOR_FIELDS] + [account_id]
                    cur.execute(
                        f'UPDATE "CustomerVendor" SET {set_clause} WHERE "AccountID" = %s',
                        params,
                    )
                    msg = 'Record updated successfully'

                else:
                    # ── INSERT ────────────────────────────────────────────
                    cur.execute('SELECT MAX("AccountID") FROM "ChartOfAccounts"')
                    max_id = cur.fetchone()[0] or 0
                    account_id = max_id + 1

                    cur.execute(
                        '''
                        INSERT INTO "ChartOfAccounts"
                        ("AccountID", "MGroup", "AcCode", "Description",
                         "ArabicDesc", "GroupID", "Active", "Address1")
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ''',
                        [account_id, mgroup, ac_code, description,
                         data.get('ArabicDesc'), group_id, active, data.get('Address1')],
                    )

                    cols = '"AccountID", ' + ', '.join([f'"{f}"' for f in CUSTOMER_VENDOR_FIELDS])
                    vals = '%s, ' + ', '.join(['%s'] * len(CUSTOMER_VENDOR_FIELDS))
                    params = [account_id] + [data.get(f) for f in CUSTOMER_VENDOR_FIELDS]
                    cur.execute(
                        f'INSERT INTO "CustomerVendor" ({cols}) VALUES ({vals})',
                        params,
                    )
                    msg = 'Record created successfully'

        return JsonResponse({'success': True, 'message': msg})

    except Exception as e:
        logger.error('save_party error: %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


def load_party(request, mgroup: int) -> JsonResponse:
    """Load a single party record by AcCode and mgroup."""
    ac_code = request.GET.get('AcCode', '').strip()
    if not ac_code:
        return JsonResponse({'success': False, 'error': 'Account Code required'})

    db_alias = _get_db(request)
    ensure_party_tables(db_alias)

    try:
        with connections[db_alias].cursor() as cur:
            cur.execute(
                '''
                SELECT c."AccountID", c."AcCode", c."Description", c."ArabicDesc",
                       c."GroupID", c."Active", c."Address1", v.*
                FROM "ChartOfAccounts" c
                LEFT JOIN "CustomerVendor" v ON c."AccountID" = v."AccountID"
                WHERE c."AcCode" = %s AND c."MGroup" = %s
                ''',
                [ac_code, mgroup],
            )
            row = cur.fetchone()

        if not row:
            return JsonResponse({'success': False, 'error': 'Record not found'})

        cols = [col[0] for col in cur.description]
        data = dict(zip(cols, row))
        data['Active'] = bool(data.get('Active'))

        return JsonResponse({'success': True, 'data': data})

    except Exception as e:
        logger.error('load_party error: %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


def delete_party(request, mgroup: int) -> JsonResponse:
    """Delete a party record by AcCode (passed as pk) and mgroup."""
    ac_code = request.GET.get('pk', '').strip()
    db_alias = _get_db(request)
    ensure_party_tables(db_alias)

    try:
        with transaction.atomic(using=db_alias):
            with connections[db_alias].cursor() as cur:
                cur.execute(
                    'SELECT "AccountID" FROM "ChartOfAccounts" WHERE "AcCode"=%s AND "MGroup"=%s',
                    [ac_code, mgroup],
                )
                row = cur.fetchone()
                if not row:
                    return JsonResponse({'success': False, 'error': 'Not found'})

                account_id = row[0]
                cur.execute('DELETE FROM "CustomerVendor" WHERE "AccountID"=%s', [account_id])
                cur.execute('DELETE FROM "ChartOfAccounts" WHERE "AccountID"=%s', [account_id])

        return JsonResponse({'success': True, 'message': 'Record deleted'})

    except Exception as e:
        logger.error('delete_party error: %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


def lookup_party(request, mgroup: int) -> JsonResponse:
    """Return a filtered list of party codes and names for lookup/autocomplete."""
    q = request.GET.get('q', '').strip()
    db_alias = _get_db(request)
    ensure_party_tables(db_alias)

    try:
        with connections[db_alias].cursor() as cur:
            sql = 'SELECT "AcCode", "Description" FROM "ChartOfAccounts" WHERE "MGroup"=%s'
            params = [mgroup]
            if q:
                sql += ' AND ("AcCode" ILIKE %s OR "Description" ILIKE %s)'
                params.extend([f'%{q}%', f'%{q}%'])
            sql += ' LIMIT 50'

            cur.execute(sql, params)
            results = [{'id': r[0], 'text': f'{r[0]} - {r[1]}'} for r in cur.fetchall()]

        return JsonResponse({'success': True, 'results': results})

    except Exception as e:
        logger.error('lookup_party error: %s', e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})
