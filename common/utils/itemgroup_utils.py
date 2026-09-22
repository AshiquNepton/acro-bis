# common/utils/itemgroup_utils.py
"""
ItemGroup Resolver — shared utility for type-19 (searchable-dropdown) fields.
=============================================================================

All type-19 form fields that store a GroupID from the ``ItemGroups`` table
(UOM, Packing, Brand, Category, Warehouse, Country, etc.) should resolve their
value through ``resolve_itemgroup`` before saving to any master table.

Usage (inside any view save function)
--------------------------------------
    from common.utils.itemgroup_utils import resolve_itemgroup, resolve_itemgroup_fields

    # Single field:
    with connections[db].cursor() as cur:
        post['PackingDetails'] = resolve_itemgroup(cur, typecode=129, val=post.get('PackingDetails'))

    # Multiple fields at once:
    FIELD_TYPECODES = {
        'BaseUnit'      : 9,
        'PurchaseUnit'  : 9,
        'SalesUnit'     : 9,
        'PackingDetails': 129,
        'ItemGroup1'    : 1,
    }
    with connections[db].cursor() as cur:
        resolve_itemgroup_fields(cur, post, FIELD_TYPECODES)

Typecode reference (add new codes here as the project grows)
-------------------------------------------------------------
    9   – Unit of Measure (UOM)
    1   – Item Group 1
    29  – Item (root group)
    30  – Item Group 2
    31  – Item Group 3
    129 – Packing Type
    201 – Item Group 4
    202 – Item Group 5
    2   – Category
    4   – Brand
    7   – Tax Group
    16  – Warehouse
    3   – Company
    138 – Country of Origin
    130 – Department
    131 – Section
    132 – Family
    133 – Flavour
    134 – Color
"""

import logging

logger = logging.getLogger(__name__)

# Maximum insert retry attempts on concurrent GroupID collisions
_MAX_RETRIES = 5


def resolve_itemgroup(cur, typecode: int, val) -> str:
    """
    Resolve a type-19 field value to a numeric ``GroupID`` string.

    Rules
    -----
    * If *val* is empty / None  → returns ``''``  (no group assigned).
    * If *val* is already a digit string → returns it unchanged (already a GroupID).
    * Otherwise treats *val* as a **Description** label:
        1. Looks up ``ItemGroups WHERE Category=typecode AND Description ILIKE val``.
        2. Falls back to a description-only search (any category) if not found.
        3. Auto-inserts a new ``ItemGroups`` row with ``Category=typecode``
           if still not found, using a concurrency-safe MAX(GroupID)+1 strategy
           with up to ``_MAX_RETRIES`` retries.

    Parameters
    ----------
    cur       : An open database cursor (must be within an active transaction).
    typecode  : The ``Category`` value that identifies the group type in ``ItemGroups``.
    val       : The raw form value — either a numeric GroupID or a text label.

    Returns
    -------
    str  — the resolved GroupID as a string, or ``''`` if val was empty.
    """
    if val is None:
        return ''
    s_val = str(val).strip()
    if not s_val:
        return ''

    # Already a numeric ID — trust it as-is
    if s_val.isdigit():
        return s_val

    # ── 1. Exact match within the correct category ──────────────────────────
    cur.execute(
        'SELECT "GroupID" FROM "ItemGroups" '
        'WHERE "Category" = %s AND LOWER("Description") = LOWER(%s) LIMIT 1',
        [typecode, s_val],
    )
    row = cur.fetchone()
    if row:
        return str(row[0])

    # ── 2. Description-only fallback (any category) ─────────────────────────
    cur.execute(
        'SELECT "GroupID" FROM "ItemGroups" '
        'WHERE LOWER("Description") = LOWER(%s) LIMIT 1',
        [s_val],
    )
    row = cur.fetchone()
    if row:
        return str(row[0])

    # ── 3. Auto-insert with concurrency-safe retry ──────────────────────────
    new_id = None
    for attempt in range(_MAX_RETRIES):
        try:
            cur.execute('SELECT COALESCE(MAX("GroupID"), 0) + 1 FROM "ItemGroups"')
            new_id = cur.fetchone()[0]
            cur.execute(
                'INSERT INTO "ItemGroups" ("GroupID", "Category", "Description") '
                'VALUES (%s, %s, %s)',
                [new_id, typecode, s_val],
            )
            logger.info(
                'resolve_itemgroup: inserted "%s" → GroupID=%s (Category=%s)',
                s_val, new_id, typecode,
            )
            return str(new_id)
        except Exception:
            # Another process may have inserted the same ID — re-check
            cur.execute(
                'SELECT "GroupID" FROM "ItemGroups" '
                'WHERE "Category" = %s AND LOWER("Description") = LOWER(%s) LIMIT 1',
                [typecode, s_val],
            )
            row = cur.fetchone()
            if row:
                return str(row[0])
            logger.debug(
                'resolve_itemgroup: collision on attempt %d for "%s" (Category=%s), retrying…',
                attempt + 1, s_val, typecode,
            )

    # Last-resort fallback — return whatever new_id was computed last
    logger.warning(
        'resolve_itemgroup: exhausted retries for "%s" (Category=%s), returning %s',
        s_val, typecode, new_id,
    )
    return str(new_id) if new_id is not None else ''


def resolve_itemgroup_fields(cur, post: dict, field_typecodes: dict) -> None:
    """
    Resolve multiple type-19 fields in *post* in one cursor pass.

    Parameters
    ----------
    cur              : An open database cursor.
    post             : The mutable POST data dict (modified in-place).
    field_typecodes  : Mapping of ``{field_name: typecode}``.

    Example
    -------
        PACKING_FIELDS = {'PackingDetails': 129}
        UOM_FIELDS     = {'BaseUnit': 9, 'PurchaseUnit': 9, 'SalesUnit': 9}

        with connections[db].cursor() as cur:
            resolve_itemgroup_fields(cur, post, {**UOM_FIELDS, **PACKING_FIELDS})
    """
    for field_name, typecode in field_typecodes.items():
        raw = post.get(field_name, '')
        post[field_name] = resolve_itemgroup(cur, typecode, raw)
