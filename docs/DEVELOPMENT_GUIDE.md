# ACRO-BIS Developer & Modular Restructuring Guide

This document establishes the official developer rules for adding or modifying features in **ACRO-BIS**.

As the project grows into multiple business verticals (**Inventory**, **Laundry**, **Restaurant**, **Financial**, etc.), developers must strictly separate **Shared (Common)** logic from **Domain-Specific (Vertical)** logic.

---

## 1. Where Does My Code Belong? (Decision Checklist)

Before writing any new file or function, consult this table:

| If your code is... | Where it belongs | Example |
|---|---|---|
| Authentication, Session, or Tenant DB routing | `common/middleware/` | `DynamicDatabaseMiddleware`, `AuthenticationMiddleware` |
| Universal database operations (infrastructure) | `core/crud.py` | `BaseCRUD` |
| Global UI, styling, base layouts | `common/templates/common/` & `common/static/common/` | `base.html`, `profile_form.html`, `colors.css`, `profile_form.js` |
| A capability used across 2+ verticals | `common/services/` | `DataFetcher`, `UniversalInventoryService`, `party_service.py` |
| Cross-vertical masters (enterprise info) | `common/models/` & `common/views/` | `Organization`, `FirmMaster`, `ChartOfAccounts` |
| Technical utilities (form builders, context) | `common/utils/` | `profile_form_helpers.py`, `context_utils.py` |
| Central exceptions & error handlers | `errors/` | `exceptions.py`, `handlers.py` |
| External API surface | `api/` | `api/views/`, `api/serializers/` |
| Cross-module reporting/export | `reports/` | `reports/views/`, `reports/utils/` |
| Specific to ONE business vertical | `<vertical_name>/` | `inventory/views/item_master.py`, `laundry/views/orders.py` |

See `ARCHITECTURE.md` for the full `core/` vs `common/` distinction.

---

## 2. Directory Separation Rules

### A. Shared Platform (`common/`, `core/`, `errors/`)
- **Strict rule**: shared platform files must **NEVER** import or refer to any specific vertical (`common` must never import `inventory`, `laundry`, or `restaurant`).
- If you write a helper function in a vertical and notice another vertical could use it, **move it to `common/services/` immediately**.

### B. Business Verticals (`inventory/`, `laundry/`, `restaurant/`, `financial/`, etc.)
- **Strict rule**: verticals must **NEVER** import each other directly (`laundry` must not import from `inventory`).
- When a vertical needs inventory tracking, accounting entries, or paginated queries, it **must** call the common services:

```python
from common.services.inventory_service import UniversalInventoryService
from common.services.accounting_service import UniversalAccountingService
from common.services.data_fetcher import DataFetcher
```

### C. Presentation Layers (`api/`, `reports/`)
- `api/` views call vertical/common services — they don't hold business logic themselves.
- `reports/` reads via `DataFetcher` and shared services — it never writes transactional data or reimplements accounting/inventory logic.

---

## 3. Standard Recipe for Adding a New CRUD/Master Screen

1. **Do NOT create custom CSS** — inherit from `common/base.html` and the shared design system.
2. **Define the screen via Python** (`views/<feature>.py`):
   Use `build_form_config()`, `build_hero_config()`, and `field()` from `common/utils/profile_form_helpers.py`.
3. **Use a paper-thin template** (`templates/<vertical>/<feature>/form.html`):

```html
{% extends 'common/base.html' %}
{% block title %}{{ form_config.title }}{% endblock %}

{% block content %}
<form id="{{ form_config.form_id }}" method="post" autocomplete="off">
    {% csrf_token %}
    {% include 'common/includes/profile_form.html' with fc=form_config %}
</form>
{% endblock %}

{% block extra_js %}
<script src="{% static 'common/js/profile_form.js' %}"></script>
<script>
window._pfConfig = {
    '{{ form_config.form_id }}': {
        lookupField: 'code',
        heroNameField: 'name'
    }
};
</script>
{% endblock %}
```

4. **Use `DataFetcher` for all queries** — never write unbounded `.all()` on large tables; use `DataFetcher.fetch_paginated()`.

*(For a specialized interactive screen like POS or KDS, skip the wrapper pattern and build a dedicated template + module-scoped JS/CSS instead).*

---

## 4. Before Creating a New File

Work through this checklist in order:
1. Search the existing project for similar functionality.
2. Check `common/` and `core/`.
3. Check `common/services/`.
4. Check `common/utils/`.
5. Check whether an existing helper/service can be reused instead of writing a new one.
6. Check whether the functionality belongs to an existing vertical rather than a new file.
7. Only then create a new file. Do not create duplicate utilities.

---

## 5. Summary Checklist for Code Reviews

- [ ] Are credentials absent from the code?
- [ ] Is there zero inline `<style>` and zero per-*form* CSS files?
- [ ] Is common functionality placed in `common/` rather than copied into a vertical?
- [ ] Are exceptions using `errors/exceptions.py`?
- [ ] Are database operations wrapped using `core.crud.BaseCRUD` or `DataFetcher`?
- [ ] Does the change avoid runtime table creation (migrations only — see `DATABASE_GUIDE.md`)?
- [ ] Is the Python code simple, readable, and well-commented for beginners?

---

## 6. Collaborator Onboarding: How to Code for Beginners

1. **You don't need advanced metaclasses or CSS** — the UI layout is rendered by the shared system for CRUD screens. You write standard Python dictionaries (`form_config`) specifying labels, fields, and tabs.
2. **Comment your thought process** — explain *why* a calculation or check is done:

```python
# Deduct 5% early payment discount if paid within 7 days
if days_since_invoice <= 7:
    discount = total_amount * Decimal('0.05')
```

3. **Keep functions short and focused where practical** — each function should do one clear job.
4. **Ask questions early** — if unsure whether something belongs in `common/` or a vertical, check §1 of this guide before writing duplicate code.