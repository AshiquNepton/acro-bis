"""
Universal CRUD helper for all modules (laundry, restaurant, inventory, financial).

Auto-creates missing tables on first use if a table_creator callable is provided.

── Unified field map format ────────────────────────────────────────────────────

Each entry in field_map combines the form-field name AND the column type in one
place, so you never have to maintain two separate dicts:

    FIELD_MAP = {
        'RegNo'   : ('reg_no',    'str'),
        'EmpName' : ('emp_name',  'str'),
        'DOB'     : ('dob',       'date'),
        'Active'  : ('active',    'int'),
        'BasicPay': ('basic_pay', 'float'),
    }

Accepted type tokens: 'str' (default), 'int', 'float', 'date', 'time', 'bool'

The old two-dict style is still accepted for backwards compatibility:
    field_map = {'RegNo': 'reg_no', ...}
    col_types = {'DOB': 'date', ...}          # optional second dict

── Duplicate-check usage ────────────────────────────────────────────────────────

Pass `unique_fields` to save() to block duplicate INSERTs automatically:

    # Single field
    crud.save(request.POST, unique_fields=[('FName', 'dept_name')])

    # Multi-field combo (name + parent must be unique together)
    crud.save(request.POST, unique_fields=[('FName', 'dept_name'), ('Under', 'under')])

You can also call check_duplicate() directly from a view for live/blur checks:

    result = crud.check_duplicate(
        unique_fields=[('FName', dept_name_value)],   # (db_col, raw_value)
        exclude_pk=current_firm_id,                    # None for new records
    )
    # result = {'is_duplicate': True/False, 'existing_pk': <val or None>}

── Usage ───────────────────────────────────────────────────────────────────────

    from core.crud import BaseCRUD

    crud = BaseCRUD(
        table         = 'Items',
        pk_col        = 'ItemCode',
        field_map     = FIELD_MAP,          # unified format
        db_alias      = get_customer_db(),
        required      = ['item_name', 'item_code'],
        table_creator = ensure_items_table,
    )
"""

import logging
import re
from datetime import datetime, date
from contextlib import contextmanager
from django.db import connections, ProgrammingError, DataError, transaction, IntegrityError
from django.db.utils import ConnectionDoesNotExist
from django.http import JsonResponse

logger = logging.getLogger(__name__)


# ─── Bidirectional label ↔ int maps ──────────────────────────────────────────
_STR_TO_INT = {
    'yes': 1, 'true': 1, 'on': 1, 'active': 1,
    'no': 0, 'false': 0, 'off': 0, 'inactive': 0,
    'male': 1, 'female': 0,
    'single': 0, 'married': 1, 'divorced': 2,
}

_INT_TO_STR_BY_COL = {
    'Active'       : {1: 'Active',  0: 'Inactive'},
    'HRStatus'     : {1: 'Active',  0: 'Inactive'},
    'Gender'       : {1: 'Male',    0: 'Female'},
    'MaritalStatus': {0: 'Single',  1: 'Married', 2: 'Divorced'},
}


# ─── Type coercion helpers ────────────────────────────────────────────────────

def _coerce(value, col_type):
    if value is None:
        return None

    value = str(value).strip()

    if value == '':
        return None

    if col_type == 'int':
        normalised = value.lower()
        if normalised in _STR_TO_INT:
            return _STR_TO_INT[normalised]
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValueError(f'Expected integer, got "{value}"')

    if col_type == 'float':
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ValueError(f'Expected number, got "{value}"')

    if col_type == 'date':
        if isinstance(value, (date, datetime)):
            return value if isinstance(value, date) else value.date()
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError(f'Expected YYYY-MM-DD date, got "{value}"')

    if col_type == 'time':
        return value

    if col_type == 'bool':
        return 1 if value.lower() in ('1', 'true', 'on', 'yes') else 0

    return value


def _safe(value, db_col=None):
    """
    Serialise a Python value to something JSON-safe.
    Reverse-maps ints to human labels for known columns (Active, Gender, …).
    """
    if db_col and isinstance(value, int) and db_col in _INT_TO_STR_BY_COL:
        label = _INT_TO_STR_BY_COL[db_col].get(value)
        if label is not None:
            return label
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(value, date):
        return value.strftime('%Y-%m-%d')
    return value


# ─── Field-map parser ─────────────────────────────────────────────────────────

def _parse_field_map(field_map, col_types=None):
    parsed_field_map = {}
    parsed_col_types = dict(col_types or {})

    for db_col, spec in field_map.items():
        if isinstance(spec, tuple):
            form_field = spec[0]
            col_type   = spec[1] if len(spec) > 1 else 'str'
            parsed_field_map[db_col] = form_field
            parsed_col_types.setdefault(db_col, col_type)
        else:
            parsed_field_map[db_col] = spec

    return parsed_field_map, parsed_col_types


# ─── Length-error resolver ────────────────────────────────────────────────────

def _resolve_length_errors(exc, table, db_alias, db_data, field_map):
    errors = []

    col_limits = {}
    try:
        with connections[db_alias].cursor() as cur:
            cur.execute(
                """
                SELECT column_name, character_maximum_length
                FROM   information_schema.columns
                WHERE  table_name = %s
                  AND  character_maximum_length IS NOT NULL
                """,
                [table]
            )
            for col_name, max_len in cur.fetchall():
                col_limits[col_name] = int(max_len)
    except Exception:
        pass

    if col_limits:
        for db_col, value in db_data.items():
            if not isinstance(value, str):
                continue
            limit = col_limits.get(db_col)
            if limit is None:
                continue
            actual = len(value)
            if actual > limit:
                form_field = field_map.get(db_col, db_col)
                errors.append({
                    'field'  : form_field,
                    'db_col' : db_col,
                    'limit'  : limit,
                    'actual' : actual,
                    'message': f'Max {limit} characters (you entered {actual})',
                })

    if not errors:
        m = re.search(r'character varying\((\d+)\)', str(exc))
        limit = int(m.group(1)) if m else None
        for db_col, value in db_data.items():
            if not isinstance(value, str):
                continue
            actual = len(value)
            if limit and actual > limit:
                form_field = field_map.get(db_col, db_col)
                errors.append({
                    'field'  : form_field,
                    'db_col' : db_col,
                    'limit'  : limit,
                    'actual' : actual,
                    'message': f'Max {limit} characters (you entered {actual})',
                })

    return errors


# ─── Identity-column detection ────────────────────────────────────────────────

def _is_identity_column(db_alias, table, pk_col):
    """
    Return True if pk_col on table is a PostgreSQL identity column
    (GENERATED ALWAYS or GENERATED BY DEFAULT).

    Cached per (db_alias, table, pk_col) so we only hit the DB once.
    """
    cache_key = (db_alias, table, pk_col)
    if cache_key in _is_identity_column._cache:
        return _is_identity_column._cache[cache_key]

    result = False
    try:
        with connections[db_alias].cursor() as cur:
            cur.execute(
                """
                SELECT is_identity
                FROM   information_schema.columns
                WHERE  table_schema = 'public'
                AND    table_name   = %s
                AND    column_name  = %s
                """,
                [table, pk_col]
            )
            row = cur.fetchone()
            result = bool(row and row[0] == 'YES')
    except Exception:
        pass

    _is_identity_column._cache[cache_key] = result
    return result

_is_identity_column._cache = {}

# In-memory table verification cache to eliminate repetitive DDL round trips
_ENSURED_TABLES = set()


def clear_ensured_table_cache(db_alias=None, table=None):
    """Clear cached table existence checks (used when schema changes or on retry)."""
    global _ENSURED_TABLES
    if db_alias and table:
        _ENSURED_TABLES.discard((db_alias, table))
    elif db_alias:
        _ENSURED_TABLES = {k for k in _ENSURED_TABLES if k[0] != db_alias}
    else:
        _ENSURED_TABLES.clear()


@contextmanager
def safe_atomic(db_alias: str):
    """
    Context manager that safely executes a block inside transaction.atomic(using=db_alias).
    Falls back to no-op if db_alias is unregistered or mocked during unit tests.
    """
    try:
        from django.db import connections as dj_connections
        if (
            db_alias
            and hasattr(dj_connections, 'databases')
            and db_alias in dj_connections.databases
        ):
            with transaction.atomic(using=db_alias):
                yield
            return
    except ConnectionDoesNotExist:
        pass
    yield


# ─── BaseCRUD ─────────────────────────────────────────────────────────────────

class BaseCRUD:
    """
    Parameters
    ----------
    table         : str   — DB table name, e.g. 'Employees'
    pk_col        : str   — Primary-key DB column, e.g. 'RegNo'
    field_map     : dict  — Unified or legacy format (see module docstring)
    db_alias      : str   — Django database alias (default 'customer_db')
    col_types     : dict  — Optional override map {'DbCol': 'type'}
    required      : list  — Form field names that must be non-empty on save
    table_creator : callable — fn(db_alias) → bool, auto-creates table when missing

    preserve_empty_on_update : list
        Form field names whose empty-string POST value should NOT overwrite
        the existing DB value during an UPDATE.
    """

    def __init__(self, table, pk_col, field_map,
                 db_alias='customer_db', col_types=None,
                 required=None, table_creator=None,
                 preserve_empty_on_update=None):
        self.table  = table
        self.pk_col = pk_col

        self.field_map, self.col_types = _parse_field_map(field_map, col_types)

        self.rev_map                  = {v: k for k, v in self.field_map.items()}
        self.db_alias                 = db_alias
        self.required                 = required or []
        self.table_creator            = table_creator
        self.preserve_empty_on_update = set(preserve_empty_on_update or [])

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _conn(self):
        return connections[self.db_alias]

    def _atomic(self):
        return safe_atomic(self.db_alias)

    def _tbl(self):
        return f'"{self.table}"'

    def _ensure_table(self, force: bool = False):
        key = (self.db_alias, self.table)
        if not force and key in _ENSURED_TABLES:
            return
            
        try:
            with self._conn().cursor() as cur:
                cur.execute(f"SELECT * FROM {self._tbl()} LIMIT 0")
                existing_cols = {desc[0] for desc in cur.description}
                
                missing_cols = []
                for db_col, ctype in self.col_types.items():
                    if db_col != self.pk_col and db_col not in existing_cols:
                        missing_cols.append(db_col)
                
                if missing_cols:
                    for col in missing_cols:
                        ctype = self.col_types.get(col, 'str')
                        sql_type = 'VARCHAR(255)'
                        if ctype == 'int': sql_type = 'INTEGER'
                        elif ctype == 'float': sql_type = 'NUMERIC(14, 4)'
                        elif ctype == 'date': sql_type = 'DATE'
                        elif ctype == 'time': sql_type = 'TIME'
                        elif ctype == 'bool': sql_type = 'INTEGER'
                        
                        cur.execute(f'ALTER TABLE {self._tbl()} ADD COLUMN "{col}" {sql_type}')
                    logger.info('[BaseCRUD] Auto-altered table "%s", added columns: %s', self.table, missing_cols)
                    
            _ENSURED_TABLES.add(key)
        except ProgrammingError as e:
            if 'does not exist' in str(e).lower():
                if self.table_creator:
                    try:
                        created = self.table_creator(self.db_alias)
                        _ENSURED_TABLES.add(key)
                        if created:
                            logger.info('[BaseCRUD] Auto-created table "%s" via creator', self.table)
                    except Exception as ex:
                        logger.warning('Table creator failed: %s', ex)
                else:
                    cols_def = [f'"{self.pk_col}" SERIAL PRIMARY KEY']
                    for col, ctype in self.col_types.items():
                        if col == self.pk_col: continue
                        sql_type = 'VARCHAR(255)'
                        if ctype == 'int': sql_type = 'INTEGER'
                        elif ctype == 'float': sql_type = 'NUMERIC(14, 4)'
                        elif ctype == 'date': sql_type = 'DATE'
                        elif ctype == 'time': sql_type = 'TIME'
                        elif ctype == 'bool': sql_type = 'INTEGER'
                        cols_def.append(f'"{col}" {sql_type}')
                    
                    create_sql = f'CREATE TABLE {self._tbl()} (\n    ' + ',\n    '.join(cols_def) + '\n)'
                    try:
                        with self._conn().cursor() as cur:
                            cur.execute(create_sql)
                        _ENSURED_TABLES.add(key)
                        logger.info('[BaseCRUD] Auto-created table "%s" dynamically', self.table)
                    except Exception as ex:
                        logger.warning('Dynamic table creation failed: %s', ex)
            else:
                logger.warning('[BaseCRUD._ensure_table] %s on %s: %s', self.table, self.db_alias, e)
        except Exception as e:
            logger.warning('[BaseCRUD._ensure_table] %s on %s: %s', self.table, self.db_alias, e)

    def _row_to_dict(self, cols, row):
        result = {}
        for col, val in zip(cols, row):
            form_field = self.field_map.get(col, col)
            result[form_field] = _safe(val, db_col=col)
        return result

    def _post_to_db(self, post_data, is_update=False):
        db_data = {}
        for form_field, db_col in self.rev_map.items():
            if form_field not in post_data:
                continue
            raw     = post_data.get(form_field)
            raw_str = str(raw).strip() if raw is not None else ''

            if is_update and raw_str == '' and form_field in self.preserve_empty_on_update:
                continue

            col_type        = self.col_types.get(db_col, 'str')
            db_data[db_col] = _coerce(raw, col_type)
        return db_data

    def _validate(self, post_data):
        return [
            f for f in self.required
            if not str(post_data.get(f) or '').strip()
        ]

    @staticmethod
    def _pk_val(value):
        if value is None:
            return None
        s = str(value).strip()
        return s if s else None

    # ── Duplicate check ───────────────────────────────────────────────────────

    def check_duplicate(self, unique_fields, exclude_pk=None):
        """
        Check whether a record already exists that matches ALL of the given
        field values (AND logic — every field must match).

        Parameters
        ----------
        unique_fields : list of (db_col, raw_value)
            Each tuple is one column to match.  Pass multiple tuples for a
            compound-unique constraint (e.g. name + parent).

            Examples
            ────────
            # Single field
            crud.check_duplicate([('FName', 'Accounts')])

            # Multi-field combo
            crud.check_duplicate([('FName', 'Accounts'), ('Under', 3)])

        exclude_pk : str | int | None
            When editing an existing record, pass its PK so the row does not
            flag itself as a duplicate.  Pass None for new records.

        Returns
        -------
        dict
            {
                'is_duplicate' : bool,
                'existing_pk'  : <pk value or None>,
                'matched_fields': [(db_col, value), …],   # which fields matched
            }

        Raises
        ------
        Exception — let the caller decide how to surface DB errors.
        """
        if not unique_fields:
            return {'is_duplicate': False, 'existing_pk': None, 'matched_fields': []}

        self._ensure_table()

        # ── Build WHERE clause ────────────────────────────────────────────
        conditions = []
        params     = []

        for db_col, raw_value in unique_fields:
            col_type  = self.col_types.get(db_col, 'str')
            coerced   = _coerce(raw_value, col_type)

            if coerced is None:
                # A None/empty value can never form a meaningful duplicate;
                # skip it so we don't match NULLs across records.
                continue

            # Case-insensitive match for text columns
            if col_type in ('str', '') or col_type not in ('int', 'float', 'date', 'time', 'bool'):
                conditions.append(f'LOWER("{db_col}") = LOWER(%s)')
            else:
                conditions.append(f'"{db_col}" = %s')

            params.append(coerced)

        if not conditions:
            # Nothing meaningful to check (all values were empty)
            return {'is_duplicate': False, 'existing_pk': None, 'matched_fields': []}

        where = ' AND '.join(conditions)

        # ── Exclude the current record on UPDATE ──────────────────────────
        if exclude_pk is not None:
            where  += f' AND "{self.pk_col}" != %s'
            params.append(exclude_pk)

        sql = f'SELECT "{self.pk_col}" FROM {self._tbl()} WHERE {where} LIMIT 1'

        with self._conn().cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()

        if row:
            return {
                'is_duplicate' : True,
                'existing_pk'  : row[0],
                'matched_fields': [(dc, rv) for dc, rv in unique_fields],
            }

        return {'is_duplicate': False, 'existing_pk': None, 'matched_fields': []}

    # ── Public API ────────────────────────────────────────────────────────────

    def get(self, pk_value):
        pk_value = self._pk_val(pk_value)
        try:
            self._ensure_table()
            sql = f'SELECT * FROM {self._tbl()} WHERE "{self.pk_col}" = %s'
            with self._conn().cursor() as cur:
                cur.execute(sql, [pk_value])
                row = cur.fetchone()
                if not row:
                    return JsonResponse({'success': False, 'error': 'Record not found'})
                cols = [d[0] for d in cur.description]
                return JsonResponse({'success': True, 'data': self._row_to_dict(cols, row)})
        except Exception as e:
            logger.error('[BaseCRUD.get] %s – %s', self.table, e, exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})

    def save(self, post_data, unique_fields=None, is_new: bool = None):
        """
        INSERT or UPDATE based on client intent and PK existence with concurrency protection.

        Parameters
        ----------
        post_data     : dict-like (request.POST)
        unique_fields : list of (db_col, form_field_name) | None
        is_new        : bool | None (True=INSERT, False=UPDATE, None=auto-detect)
        """
        import time
        from django.db import transaction, IntegrityError
        _t         = time.time
        _elapsed   = lambda start: f'{((_t() - start) * 1000):.1f}ms'
        save_start = _t()
        form_name  = self.table

        print(f'\n+-- SAVING  [{form_name}] ----------------------------')

        try:
            # ── Step 1: Validate required fields ──────────────────────────
            t1      = _t()
            missing = self._validate(post_data)
            if missing:
                print(f'|  [ERROR] Validation failed  ({_elapsed(t1)})')
                print(f'|    Missing: {", ".join(missing)}')
                print(f'+-- ABORTED  [{form_name}] -----------------------------\n')
                return JsonResponse({
                    'success': False,
                    'error'  : f'Required fields missing: {", ".join(missing)}'
                })
            print(f'|  [OK] Validation passed  ({_elapsed(t1)})')

            # ── Step 2: Read PK from POST ─────────────────────────────────
            pk_form_field = next(
                (f for f, c in self.rev_map.items() if c == self.pk_col), None
            )
            pk_value = self._pk_val(
                post_data.get(pk_form_field, '') if pk_form_field else ''
            )
            print(f'|  [INFO] PK  {self.pk_col} = {pk_value!r}')

            # ── Step 3: Ensure table exists ───────────────────────────────
            t3 = _t()
            self._ensure_table()
            print(f'|  [OK] Table ready  ({_elapsed(t3)})')

            # ── Step 4: Determine client intent & INSERT vs UPDATE ────────
            t4 = _t()
            if is_new is None:
                raw_is_new = post_data.get('_is_new')
                if raw_is_new is None:
                    raw_is_new = post_data.get('is_new')
                if raw_is_new is not None:
                    is_new = str(raw_is_new).strip() in ('1', 'true', 'True')

            already_exists = False
            with self._conn().cursor() as cur:
                if pk_value:
                    cur.execute(
                        f'SELECT 1 FROM {self._tbl()} WHERE "{self.pk_col}" = %s',
                        [pk_value]
                    )
                    already_exists = cur.fetchone() is not None

            if is_new is True:
                # Client intended to INSERT a new record.
                # If suggested pk_value was already taken by a concurrent insert,
                # reallocate next free ID so we NEVER overwrite an existing record!
                exists = False
                if already_exists:
                    pk_value = str(self.next_id_value())
                    print(f'|  [INFO] PK {self.pk_col} was already taken concurrently. Reallocated to: {pk_value}')
            elif is_new is False:
                # Client intended to UPDATE an existing record.
                if not already_exists:
                    print(f'|  [ERROR] Record with PK={pk_value} not found for update')
                    print(f'+-- ABORTED  [{form_name}] -----------------------------\n')
                    return JsonResponse({
                        'success': False,
                        'error'  : f'Record with {self.pk_col} "{pk_value}" does not exist or was deleted.'
                    })
                exists = True
            else:
                exists = already_exists

            print(f'|  [OK] Action determined: {"UPDATE" if exists else "INSERT"} (is_new={is_new})  ({_elapsed(t4)})')

            # ── Step 5: Duplicate check (INSERT only, or always if caller wants) ──
            if unique_fields:
                t5d = _t()
                resolved = []
                for db_col, form_field_name in unique_fields:
                    raw_val = post_data.get(form_field_name, '')
                    resolved.append((db_col, raw_val))

                exclude = pk_value if exists else None
                dup     = self.check_duplicate(resolved, exclude_pk=exclude)

                if dup['is_duplicate']:
                    field_labels = ', '.join(
                        f'"{self.field_map.get(dc, dc)}"'
                        for dc, _ in dup['matched_fields']
                    )
                    existing_id = dup['existing_pk']
                    print(f'|  [ERROR] Duplicate detected — existing PK={existing_id}  ({_elapsed(t5d)})')
                    print(f'+-- ABORTED  [{form_name}] -----------------------------\n')
                    return JsonResponse({
                        'success'    : False,
                        'duplicate'  : True,
                        'existing_pk': existing_id,
                        'error'      : (
                            f'A record with the same {field_labels} already exists '
                            f'(ID: {existing_id}).'
                        ),
                    })
                print(f'|  [OK] No duplicate found  ({_elapsed(t5d)})')

            # ── Step 6: Coerce POST → DB dict ─────────────────────────────
            t6      = _t()
            db_data = self._post_to_db(post_data, is_update=exists)
            if not db_data:
                print(f'|  [ERROR] No data after coercion  ({_elapsed(t6)})')
                print(f'+-- ABORTED  [{form_name}] -----------------------------\n')
                return JsonResponse({'success': False, 'error': 'No data to save'})
            print(f'|  [OK] Coercion done — {len(db_data)} field(s)  ({_elapsed(t6)})')

            # ── Step 7: INSERT or UPDATE with Concurrency Protection ───────
            t7 = _t()
            returned_pk = pk_value
            max_retries = 5

            for attempt in range(max_retries):
                try:
                    with self._atomic():
                        with self._conn().cursor() as cur:
                            if exists:
                                # UPDATE — always exclude PK from SET clause
                                update_cols = {k: v for k, v in db_data.items() if k != self.pk_col}
                                if not update_cols:
                                    print(f'|  [ERROR] Nothing to update')
                                    print(f'+-- ABORTED  [{form_name}] -----------------------------\n')
                                    return JsonResponse({'success': False, 'error': 'Nothing to update'})
                                set_clause = ', '.join(f'"{c}" = %s' for c in update_cols)
                                values     = list(update_cols.values()) + [pk_value]
                                cur.execute(
                                    f'UPDATE {self._tbl()} SET {set_clause} '
                                    f'WHERE "{self.pk_col}" = %s',
                                    values
                                )
                                action = 'updated'
                                returned_pk = pk_value
                            else:
                                pk_is_identity = (
                                    pk_value is None
                                    and _is_identity_column(self.db_alias, self.table, self.pk_col)
                                )

                                if pk_is_identity:
                                    insert_data = {k: v for k, v in db_data.items() if k != self.pk_col}
                                    print(f'|  [INFO] Identity PK detected — omitting "{self.pk_col}" from INSERT')
                                else:
                                    if pk_value is None:
                                        pk_value = str(self.next_id_value())
                                    coerced_pk = _coerce(pk_value, self.col_types.get(self.pk_col, 'int'))
                                    db_data[self.pk_col] = coerced_pk
                                    insert_data = db_data

                                cols         = list(insert_data.keys())
                                col_clause   = ', '.join(f'"{c}"' for c in cols)
                                placeholders = ', '.join(['%s'] * len(cols))

                                cur.execute(
                                    f'INSERT INTO {self._tbl()} ({col_clause}) '
                                    f'VALUES ({placeholders}) '
                                    f'RETURNING "{self.pk_col}"',
                                    list(insert_data.values())
                                )
                                row = cur.fetchone()
                                returned_pk = row[0] if row else pk_value
                                action = 'created'
                    break  # Success!
                except IntegrityError as exc:
                    err_msg = str(exc).lower()
                    is_pk_collision = (
                        not exists and (
                            'pk_' in err_msg
                            or f'"{self.pk_col.lower()}"' in err_msg
                            or f'({self.pk_col.lower()})' in err_msg
                            or 'primary key' in err_msg
                            or 'duplicate key' in err_msg
                        )
                    )
                    if is_pk_collision and attempt < max_retries - 1:
                        next_pk = str(self.next_id_value())
                        pk_value = next_pk
                        logger.warning(
                            '[BaseCRUD.save] Concurrent insert collision on %s (%s). Retrying with new PK=%s (attempt %d/%d)',
                            self.table, exc, next_pk, attempt + 1, max_retries
                        )
                        continue
                    raise

            print(f'|  [OK] Record {action}  (pk={returned_pk})  ({_elapsed(t7)})')
            print(f'+-- DONE  [{form_name}]  total: {_elapsed(save_start)} --------------\n')

            return JsonResponse({
                'success': True,
                'message': f'Record {action} successfully',
                'pk'     : returned_pk,
            })

        except ProgrammingError as e:
            if 'does not exist' in str(e).lower() or 'column' in str(e).lower():
                _ENSURED_TABLES.discard((self.db_alias, self.table))
                self._ensure_table(force=True)
                print(f'|  [WARN] Schema missing - auto-synced, please retry')
                print(f'+-- RETRYABLE  [{form_name}]  total: {_elapsed(save_start)} -----\n')
                return JsonResponse({
                    'success': False,
                    'error'  : 'Schema was just synced - please retry the save.'
                })
            print(f'|  [ERROR] ProgrammingError: {e}')
            print(f'+-- FAILED  [{form_name}]  total: {_elapsed(save_start)} -----------\n')
            logger.error('[BaseCRUD.save] %s – %s', self.table, e, exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})

        except DataError as e:
            print(f'|  [ERROR] DataError: {e}')
            print(f'+-- FAILED  [{form_name}]  total: {_elapsed(save_start)} -----------\n')
            logger.warning('[BaseCRUD.save] DataError %s – %s', self.table, e)

            _db_data = locals().get('db_data', {})
            field_errors = _resolve_length_errors(
                exc       = e,
                table     = self.table,
                db_alias  = self.db_alias,
                db_data   = _db_data,
                field_map = self.field_map,
            )

            if field_errors:
                names   = ', '.join(f['db_col'] for f in field_errors)
                summary = (
                    f'"{field_errors[0]["db_col"]}" exceeds the maximum length '
                    f'of {field_errors[0]["limit"]} characters.'
                    if len(field_errors) == 1
                    else f'{len(field_errors)} fields exceed their maximum length: {names}.'
                )
                return JsonResponse({
                    'success'     : False,
                    'error'       : summary,
                    'field_errors': field_errors,
                })

            return JsonResponse({
                'success': False,
                'error'  : f'A value is too long for its column. Detail: {e}',
            })

        except Exception as e:
            print(f'|  [ERROR] Error: {e}')
            print(f'+-- FAILED  [{form_name}]  total: {_elapsed(save_start)} -----------\n')
            logger.error('[BaseCRUD.save] %s – %s', self.table, e, exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})

    def delete(self, pk_value):
        pk_value = self._pk_val(pk_value)
        try:
            self._ensure_table()
            with self._conn().cursor() as cur:
                cur.execute(
                    f'SELECT 1 FROM {self._tbl()} WHERE "{self.pk_col}" = %s',
                    [pk_value]
                )
                if not cur.fetchone():
                    return JsonResponse({'success': False, 'error': 'Record not found'})
                cur.execute(
                    f'DELETE FROM {self._tbl()} WHERE "{self.pk_col}" = %s',
                    [pk_value]
                )
            return JsonResponse({'success': True, 'message': 'Record deleted successfully'})
        except Exception as e:
            logger.error('[BaseCRUD.delete] %s – %s', self.table, e, exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})

    def lookup(self, field, value):
        value = str(value).strip() if value is not None else value
        try:
            self._ensure_table()
            with self._conn().cursor() as cur:
                cur.execute(
                    f'SELECT * FROM {self._tbl()} WHERE "{field}" = %s',
                    [value]
                )
                row = cur.fetchone()
                if not row:
                    return JsonResponse({'success': False, 'error': 'Not found'})
                cols = [d[0] for d in cur.description]
                return JsonResponse({'success': True, 'data': self._row_to_dict(cols, row)})
        except Exception as e:
            logger.error('[BaseCRUD.lookup] %s – %s', self.table, e, exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})

    def search(self, q, search_col, display_cols=None, limit=20):
        display_cols = display_cols or [self.pk_col, search_col]
        try:
            self._ensure_table()
            col_clause = ', '.join(f'"{c}"' for c in display_cols)
            with self._conn().cursor() as cur:
                cur.execute(
                    f'SELECT {col_clause} FROM {self._tbl()} '
                    f'WHERE "{search_col}" ILIKE %s LIMIT %s',
                    [f'%{q}%', limit]
                )
                rows    = cur.fetchall()
                results = [
                    {self.field_map.get(c, c): _safe(v, db_col=c)
                     for c, v in zip(display_cols, row)}
                    for row in rows
                ]
            return JsonResponse({'success': True, 'results': results})
        except Exception as e:
            logger.error('[BaseCRUD.search] %s – %s', self.table, e, exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})

    def list(self, filters=None, order_by=None, limit=None):
        try:
            self._ensure_table()
            where_clause = ''
            params       = []
            if filters:
                conditions   = [f'"{c}" = %s' for c in filters]
                where_clause = 'WHERE ' + ' AND '.join(conditions)
                params       = list(filters.values())

            order_clause = ''
            if order_by:
                direction    = 'DESC' if order_by.startswith('-') else 'ASC'
                col          = order_by.lstrip('-')
                order_clause = f'ORDER BY "{col}" {direction}'

            limit_clause = f'LIMIT {int(limit)}' if limit else ''

            sql = (f'SELECT * FROM {self._tbl()} '
                   f'{where_clause} {order_clause} {limit_clause}')
            with self._conn().cursor() as cur:
                cur.execute(sql, params)
                cols = [d[0] for d in cur.description]
                rows = [self._row_to_dict(cols, row) for row in cur.fetchall()]
            return JsonResponse({'success': True, 'results': rows, 'count': len(rows)})
        except Exception as e:
            logger.error('[BaseCRUD.list] %s – %s', self.table, e, exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})

    def next_id_value(self) -> int:
        """
        Return MAX(pk_col) + 1 from the table with zero delay.
        Selects exact integer or numeric-text extraction based on declared column type,
        avoiding trial-and-error exception overhead and database aborts.
        """
        try:
            self._ensure_table()
            col_type = self.col_types.get(self.pk_col, 'int')

            if col_type in ('int', 'bigint', 'integer'):
                with self._conn().cursor() as cur:
                    cur.execute(
                        f'SELECT COALESCE(MAX("{self.pk_col}"), 0) + 1 '
                        f'FROM {self._tbl()}'
                    )
                    row = cur.fetchone()
                    return int(row[0]) if row else 1
            else:
                with self._conn().cursor() as cur:
                    cur.execute(
                        f'SELECT COALESCE(MAX('
                        f'  CASE WHEN "{self.pk_col}" ~ \'^[0-9]+$\' '
                        f'       THEN "{self.pk_col}"::BIGINT ELSE 0 END'
                        f'), 0) + 1 FROM {self._tbl()}'
                    )
                    row = cur.fetchone()
                    return int(row[0]) if row else 1

        except Exception as e:
            logger.error('[BaseCRUD.next_id_value] %s – %s', self.table, e, exc_info=True)
            return 1
        