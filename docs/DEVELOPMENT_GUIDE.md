# Developer & Modular Restructuring Guide

This document establishes the official developer rules for adding or modifying features in **ACRO-BIS**.
As the project grows into multiple business verticals (**Inventory**, **Laundry**, **Restaurant**, **Gym**, **Logistics**, etc.), developers must strictly separate **Shared (Common)** logic from **Domain-Specific (Vertical)** logic.

---

## 1. Where Does My Code Belong? (Decision Checklist)

Before writing any new file or function, consult this rule table:

| If your code is... | Where it belongs | Example |
| :--- | :--- | :--- |
| **Authentication, Session, or Tenant DB routing** | `common/middleware/` | `DynamicDatabaseMiddleware`, `AuthenticationMiddleware` |
| **Universal Database Operations** | `core/crud.py` | `BaseCRUD` |
| **Global UI, Styling, Base Layouts** | `common/templates/common/` & `common/static/` | `base.html`, `profile_form.html`, `colors.css`, `profile_form.js` |
| **A capability used across 2 or more verticals** | `common/services/` | `DataFetcher`, `UniversalInventoryService`, `UniversalAccountingService` |
| **Cross-vertical Masters (Enterprise info)** | `common/models/` & `common/views/` | `Organization` (Company), `FirmMaster` (Job/Dept), Users |
| **Central Exceptions & Error Handlers** | `errors/` | `exceptions.py`, `handlers.py` |
| **Specific ONLY to one business type** | `<module_name>/` | `inventory/views/item_master.py`, `laundry/views/orders.py`, `restaurant/views/pos.py` |

---

## 2. Directory Separation Rules

### A. Shared Platform (`common/`, `core/`, `errors/`)
- **Strict Rule**: Shared platform files must **NEVER** import or refer to any specific vertical (e.g. `common` must never import `inventory`, `laundry`, or `restaurant`).
- If you write a helper function in a vertical and notice another vertical could use it, **immediately move it to `common/`**.

### B. Business Verticals (`inventory/`, `laundry/`, `restaurant/`, etc.)
- **Strict Rule**: Verticals must **NEVER** import each other directly (e.g. `laundry` must not import from `inventory`).
- When a vertical needs inventory tracking, accounting entries, or paginated queries, it **must** call the common services:
  ```python
  from common.services.inventory_service import UniversalInventoryService
  from common.services.accounting_service import UniversalAccountingService
  from common.services.data_fetcher import DataFetcher
  ```

---

## 3. Standard Recipe for Adding a New Screen in ANY Vertical

Whenever you or any developer creates a new screen (e.g. for Gym, Logistics, POS):

1. **Do NOT create custom CSS**:
   - Every screen inherits from `common/base.html` and `profile_form.html`.
2. **Define the Screen via Python (`views/<feature>_master.py`)**:
   - Use `build_form_config()`, `build_hero_config()`, and `field()` from `common/views/profile_form_helpers.py`.
3. **Use a Paper-Thin Template (`templates/<module>/<feature>_form.html`)**:
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
4. **Use `DataFetcher` for all queries**:
   - Never write unbounded `.all()` queries on large tables. Always use `DataFetcher.fetch_paginated()`.

---

## 4. Summary Checklist for Code Reviews
- [ ] Are credentials absent from the code?
- [ ] Is there zero inline `<style>` and zero per-screen CSS files?
- [ ] Is common functionality placed in `common/` rather than copied into a vertical?
- [ ] Are exceptions using `errors/exceptions.py`?
- [ ] Are database operations wrapped using `core.crud.BaseCRUD` or `DataFetcher`?
- [ ] Is the Python code simple, readable, and well-commented for beginners?

---

## 5. Collaborator Onboarding: How to Code for Beginners

If you are a new collaborator joining this project, keep these simple guidelines in mind:

1. **You Don't Need to Know Advanced Metaclasses or CSS**:
   - The UI layout is rendered by the system.
   - You only need to write standard Python dictionaries (`form_config`) specifying what labels, fields, and tabs you want.
2. **Comment Your Thought Process**:
   - Write clear comments above blocks of business logic explaining *why* a calculation or check is done.
   - Example:
     ```python
     # Deduct 5% early payment discount if paid within 7 days
     if days_since_invoice <= 7:
         discount = total_amount * Decimal('0.05')
     ```
3. **Keep Functions Short & Focused**:
   - Each function should do one clear job (e.g. validate input, calculate totals, save record).
   - If a function exceeds 50 lines, break it into smaller helper functions with clear names.
4. **Ask Questions Early**:
   - If you are unsure whether a function should go into `common/` or a vertical module, check Section 1 of this guide or ask before writing duplicate code.

