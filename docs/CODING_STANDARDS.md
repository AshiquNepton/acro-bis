# ACRO-BIS Coding Standards & Uniformity Policy

## 1. Golden Rules

1. **Never Duplicate Code**: If logic is needed across more than one module (Laundry, Restaurant, Inventory, Financial, etc.), place it inside `common/services/` or `core/`.
2. **No Per-Screen or Per-Form CSS**: CRUD/master forms use global CSS variables (`var(--color-primary)`, `var(--color-bg-card)`, etc.) and the shared `profile_form.html` design system. Module-level CSS is allowed only for genuinely module-specific interactive screens (POS, KDS).
3. **Never Hardcode Credentials**: Never write database or API credentials into code. Read strictly from `.env` or secure session variables (`request.session['db_host']`, etc.).
4. **Preserve ASCII Compatibility**: Avoid unencoded Unicode glyphs (`│`, `✔`, `⚠`) in terminal print statements to ensure clean execution across Windows and Linux environments.
5. **Keep Python Simple & Readable**: Write clear, explicit, readable code over clever or overly complex syntax. New collaborators must be able to understand the flow without guessing. Always include clear docstrings and comments explaining the *why*, not just the *what*.
6. **Schema Changes Go Through Migrations Only**: Application runtime code must never `CREATE`, `ALTER`, or `DROP` tables. See `DATABASE_GUIDE.md` for the full rule and error-handling behavior when a table is missing.

---

## 2. Naming Conventions

- **Python**: `snake_case` for functions, variables, and module filenames (`item_master.py`, `build_form_config`).
- **Database Tables & Columns**: `TitleCase` matching legacy customer database conventions (e.g., `ItemCode`, `ItemName`, `FirmMaster`, `ChartOfAccounts`).
- **HTML IDs & Classes**: `kebab-case` (`item-master-form`, `im-split-modal`).
- **JavaScript**: `camelCase` for functions and variables (`imOpenBinLocationModal`, `renderSplitLists`).

---

## 3. Standard Form Architecture (CRUD/Master Screens)

Every CRUD/master-form screen in every vertical adheres to the 3-tier profile-form contract. *(Specialized interactive screens like POS, KDS, dashboards, and reports are exempt).*

1. **Backend View (`views/<feature>.py`)**: implements `build_form_config()` using helpers from `common/utils/profile_form_helpers.py`, returning a structured dictionary with `hero`, `action_bar`, `header_fields`, `tabs`.
2. **Template (`templates/<vertical>/<feature>/form.html`)**:

```html
{% extends 'common/base.html' %}
{% block content %}
<form id="{{ form_config.form_id }}" method="post" autocomplete="off">
    {% csrf_token %}
    {% include 'common/includes/profile_form.html' with fc=form_config %}
</form>
{% endblock %}
```

3. **Client Configuration (`profile_form.js`)**:

```javascript
window._pfConfig = {
    'form-id': {
        lookupField: 'code_field',
        saveUrl: '{% url "app_name:feature_save" %}',
        heroNameField: 'name_field'
    }
};
```

---

## 4. Error Handling Standard

- Always use exceptions from `errors/exceptions.py`.
- AJAX endpoints must always return JSON with `{ "success": false, "error": "Message" }`.
- **Never** expose raw database tracebacks or sensitive server connection strings to the client.
- If required schema (a table/column) is missing, do not create it — stop the operation, log the problem server-side, and return a controlled error (see `DATABASE_GUIDE.md`).

---

## 5. Unified High-Performance Data Fetching (`DataFetcher`)

Use `common.services.data_fetcher.DataFetcher` to eliminate delay when querying large multi-tenant datasets:

- **Selective Projection (`.values(*fields)`)**: bypasses heavy Django model instance hydration.
- **Efficient Pagination (LIMIT/OFFSET Windowing)**: never load entire tables into memory.
- **Streaming Iterator (`.iterator(chunk_size=1000)`)**: use `DataFetcher.stream_large_dataset()` for reports and exports.

---

## 6. Guidelines for Collaborators: Simple, Clean Python

### A. Simplicity Over Cleverness
- Prefer explicit over implicit: avoid deeply nested list comprehensions, complex metaclasses, or obscure one-liners.
- Use standard control flow: `for` loops, `if/elif/else` checks, early returns.
- Descriptive variable names: `item_quantity`, `invoice_amount` rather than `q`, `amt`.

### B. Standard Documentation Contract
Every function, class, and view must have a simple docstring:

```python
def record_stock_movement(item_code: str, quantity: float, movement_type: str) -> dict:
    """
    Records an incoming or outgoing stock movement for an inventory item.

    Parameters:
        item_code (str): Unique identifier of the item (e.g. 'ITM-001').
        quantity (float): Number of units moved.
        movement_type (str): 'IN' (purchase/return) or 'OUT' (sale/consumption).

    Returns:
        dict: {'success': True, 'remaining_stock': 45.0} or error dictionary.
    """
```

### C. Self-Explaining Form Configurations
Add section comments when declaring `form_config` dictionaries:

```python
# ── Hero Card (Top Identity Banner) ─────────────────────────
hero = build_hero_config(...)

# ── Primary Top Row Fields ──────────────────────────────────
header_fields = [...]

# ── Tabbed Detail Panes ─────────────────────────────────────
tabs = [...]
```

### D. Function Length
Functions should generally remain small and focused. However, a 60-line configuration-building dictionary is completely fine. Splitting a declarative dictionary into 5 scattered functions makes it *harder* to read. Use judgment.

---

## 7. Before Creating a File

Before creating any new file, work through this checklist:
1. Search the existing project for similar functionality.
2. Check `common/` and `core/`.
3. Check `common/services/` and `common/utils/`.
4. Check whether the functionality belongs to an existing feature file in your vertical.
5. Only then create a new file.

This directly supports the zero-duplication philosophy and the architectural protection rules.