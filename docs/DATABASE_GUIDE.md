# ACRO-BIS Database & Schema Management Guide

This document defines the safe, migration-based approach to database schema management required for this multi-tenant PostgreSQL system.

---

## 1. The Rule

> Database schema changes **MUST** be handled through migrations, or approved versioned database/schema scripts.
>
> Application runtime code **MUST NOT** automatically `CREATE`, `ALTER`, or `DROP` production tables.
>
> If a required table does not exist:
> 1. Stop the operation.
> 2. Log the schema problem server-side.
> 3. Return a controlled JSON error to the client.
> 4. Fix the database through the approved migration/setup process.

**Why:** Auto-creating tables at query time is unsafe in a multi-tenant architecture. Schema drift on one tenant's database can silently mask bugs, corrupt assumptions in `core/crud.py`'s `FIELD_MAPPING`, or create inconsistent schemas across tenants that are invisible until a report or migration fails later. Schema state should always be predictable and match what's tracked in version control.

---

## 2. Where Schema Changes Belong

- **Django migrations** (`<app>/migrations/`) are the default mechanism for any model-backed schema change. See existing examples like `common/migrations/0001_initial.py`.
- **`core/management/commands/setup_database.py`** and `core/management/commands/switch_business.py` are the approved entry points for provisioning a new tenant database or switching business context — not ad hoc runtime table creation inside a view or service.
- **`scripts/migrate.sh`** is the approved operational script for applying migrations across environments.

If a genuinely new mechanism for schema setup is needed, propose it as an Architecture Decision Record (ADR) rather than adding ad hoc creation logic inside application code.

---

## 3. Required Behavior When a Table Is Missing

```python
import logging
from core.exceptions import SchemaError

logger = logging.getLogger(__name__)

def get_records(model_cls):
    try:
        return model_cls.objects.all()
    except Exception as exc:
        # Do NOT create the table here.
        logger.error("Missing table for %s: %s", model_cls.__name__, exc)
        raise SchemaError(
            "Required table is missing. Run pending migrations for this tenant."
        ) from exc
```

- The error surfaced to the client must go through the standard JSON error contract (`errors/handlers.py`) — **never** expose a raw traceback or the underlying SQL error to the browser.
- **Multi-tenant note:** A missing table almost always means a tenant database is behind on migrations, not that the table has never existed anywhere. Log the tenant/business context alongside the error so it's actionable.

---

## 4. Multi-Tenant Migration Considerations

- Migrations must be applied per-tenant database, not just on the primary/shared database. Coordinate this through `scripts/migrate.sh` and `switch_business.py` rather than per-request logic.
- Any new shared model (in `common/models/`) that will be used across verticals should be migrated consistently across all tenant databases before the feature that depends on it ships.
- Test migrations against a representative tenant database in `tests/` before rolling out broadly.

---

## 5. Related Rules

- `CODING_STANDARDS.md` §1 — Runtime code must not create/alter schema.
- `SECURITY.md` §5 — Schema errors are logged server-side only, never exposed to the client in raw form.
- `ARCHITECTURE.md` — `core/crud.py` (`BaseCRUD`) is the only sanctioned database abstraction. Do not build parallel DB layers to work around this rule.