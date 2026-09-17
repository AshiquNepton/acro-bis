# ACRO-BIS Coding Standards & Uniformity Policy

## 1. Golden Rules
1. **Never Duplicate Code**: If logic is needed across more than one module (e.g. Laundry, Restaurant, Gym, Inventory), place it inside `common/` or `core/`.
2. **Never Create Per-Screen CSS**: All styling must use global CSS variables (`var(--color-primary)`, `var(--color-bg-card)`, etc.) and the `profile_form.html` design system.
3. **Never Hardcode Credentials**: Never write credentials into code. Read strictly from `.env` or session variables (`request.session['db_host']`, etc.).
4. **Preserve ASCII Compatibility in Terminal Logs**: Avoid unencoded Unicode glyphs (`│`, `✔`, `⚠`) in terminal print statements to ensure clean execution across Windows and Linux environments.
5. **Keep Python Simple & Readable (Beginner-Friendly)**: Write clear, explicit, readable code over clever or overly complex syntax. New collaborators and junior developers must be able to understand the flow without guessing. Always include clear docstrings and comments explaining the *why*, not just the *what*.
6. **Dynamic Table Creation**: Whenever you open or connect to a database for a specific module, always check if the required table exists. If there is no table, create it dynamically before executing queries; otherwise, use the existing table.

---

## 2. Naming Conventions
- **Python**: `snake_case` for functions, variables, and module filenames (`item_master.py`, `build_item_master_form_config`).
- **Database Tables & Columns**: `TitleCase` matching customer database conventions (e.g., `ItemCode`, `ItemName`, `FirmMaster`, `Organization`).
- **HTML IDs & Classes**: `kebab-case` (`item-master-form`, `im-split-modal`).
- **JavaScript**: `camelCase` for functions and variables (`imOpenBinLocationModal`, `renderSplitLists`).

---

## 3. Standard Form Architecture
Every form screen in every business vertical must adhere to the 3-tier profile-form contract:

1. **Backend View (`views/<module>_master.py`)**:
   - Implements `build_<module>_form_config()` returning a structured dictionary with:
     - `hero`: Card summary, avatar/icon, badges.
     - `action_bar`: Standard buttons (`Close`, `New`, `Save`, `Delete`).
     - `header_fields`: Top row primary inputs (Code, Name, Status).
     - `tabs`: Structured columns containing field definitions (`field(name, label, type, ...)`).

2. **Template (`templates/<module>/<module>_form.html`)**:
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
           saveUrl: '{% url "..." %}',
           heroNameField: 'name_field'
       }
   };
   ```

---

## 4. Error Handling Standard
- Always use exceptions from `errors/exceptions.py`.
- AJAX endpoints must always return JSON with `{ "success": false, "error": "Message" }`.
- Never expose raw database tracebacks or sensitive server connection strings to the client.

---

## 5. Unified High-Performance Data Fetching (`DataFetcher`)
To eliminate delay when querying large multi-tenant datasets, use `common.services.data_fetcher.DataFetcher`:
- **Selective Projection (`.values(*fields)`)**: Bypasses heavy Django model instance hydration.
- **Efficient Pagination (LIMIT/OFFSET Windowing)**: Never load entire tables into memory.
- **Streaming Iterator (`.iterator(chunk_size=1000)`)**: Use `DataFetcher.stream_large_dataset()` for reports and exports.

---

## 6. Guidelines for Collaborators: Simple, Clean & Documented Python

When adding or onboarding new developers to the project, follow these principles so anyone can contribute easily:

### A. Simplicity Over Cleverness
- **Prefer explicit over implicit**: Avoid deeply nested list comprehensions, complex metaclasses, or obscure one-liners.
- **Standard control flow**: Use standard `for` loops, `if/else` checks, and early returns.
- **Descriptive variable names**: Use `item_quantity`, `invoice_amount`, `customer_code` rather than `q`, `amt`, `c`.

### B. Standard Documentation Contract
Every function, class, and view must have a simple docstring structured like this:
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
When declaring `form_config` dictionaries, add section comments:
```python
# ── Hero Card (Top Identity Banner) ─────────────────────────
hero = build_hero_config(...)

# ── Primary Top Row Fields ──────────────────────────────────
header_fields = [...]

# ── Tabbed Detail Panes ─────────────────────────────────────
tabs = [...]
```
This ensures a beginner can immediately see which part of the Python dict maps to which visual part of the screen.


