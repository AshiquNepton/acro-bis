# ACRO-BIS Architecture Reference

> **Purpose:** Defines how ACRO-BIS must be organized as the system grows.
> The goal is to keep existing working code organized without weakening functionality,
> changing business behavior, or creating duplicate architecture.

---

## 1. Core Principle — Feature Ownership

Every feature has one predictable chain of ownership:

```
DATABASE TABLE
    ↓
MODEL FILE          common/models/customer.py
    ↓
SERVICE             common/services/party_service.py   (if business logic is reusable)
    ↓
FORM FILE           common/forms/customer.py
    ↓
VIEW FILE           common/views/customers.py
    ↓
URL                 common/urls.py
    ↓
TEMPLATE            common/templates/common/masters/customer/
    ↓
STATIC ASSETS       common/static/common/
```

When a developer asks *"where is the code for this feature?"* the answer must be obvious from the directory structure alone.

---

## 2. Business Verticals

| `software_id` | Vertical | Django App |
|:---:|---|---|
| 1 | Laundry & Dry Cleaning | `laundry/` |
| 2 | Restaurant & POS | `restaurant/` |
| 3 | HRMS | *(standalone)* |
| 4 | Inventory & Supply Chain | `inventory/` |
| 5 | Financial & General Ledger | `financial/` |
| 6 | Logistics & Warehousing | *(upcoming)* |
| 7 | Gym & Fitness | *(upcoming)* |

---

## 3. Dependency Direction

```
erp_project/
    │
    ▼
core/ + common/ + errors/        ← Shared platform (no vertical imports)
    │
    ▼
common/services/                 ← Shared business operations
    │
    ├──────────────┬─────────────┐
    ▼              ▼             ▼
inventory/     laundry/     restaurant/     financial/
    │              │             │
    └──────────────┴─────────────┘
                   │
                   ▼
           reports/ + api/       ← Presentation only (read-only / external)
```

**Rules:**
- `core/` and `common/` must never import from a vertical.
- Verticals must never import each other directly.
- `reports/` and `api/` must not own business logic.

---

## 4. Module Structure — Every Vertical

```
vertical/
├── models/
│   ├── __init__.py              ← re-exports all model symbols
│   └── <domain>.py              ← one file per business domain
│
├── forms/
│   ├── __init__.py
│   └── <domain>.py
│
├── views/
│   ├── __init__.py
│   └── <feature>.py             ← one file per feature area
│
├── templates/<vertical>/
│   └── <feature>/               ← subdirectory per feature
│       ├── list.html
│       ├── form.html
│       └── detail.html
│
├── static/<vertical>/
│   ├── css/
│   └── js/
│
├── admin.py
├── apps.py
└── urls.py
```

---

## 5. Model Organization

### Rule: One file per domain — never mix unrelated tables.

```python
# GOOD — inventory/models/item.py
class InventoryItem(models.Model): ...
class ItemBarcode(models.Model): ...
class ItemUnit(models.Model): ...

# BAD — inventory/models/item.py
class InventoryItem(models.Model): ...
class Supplier(models.Model): ...      # ← belongs in common/models/supplier.py
class RestaurantTable(models.Model):  # ← belongs in restaurant/models/table.py
```

### `models/__init__.py` must re-export everything:

```python
# inventory/models/__init__.py
from .category import *
from .item import *
from .purchase import *
from .stock import *
from .warehouse import *
```

---

## 6. View Organization

### File-per-feature inside `views/`:

```
inventory/views/
├── __init__.py
├── dashboard.py       ← inventory dashboard
├── items.py           ← item list, create, update, delete, AJAX lookups
├── item_master.py     ← item master profile form
├── purchase.py        ← purchase order CRUD
├── stock.py           ← stock entry, adjustment, movement
├── reports.py         ← inventory reports
├── import_view.py     ← Excel import
└── import_config.py   ← import configuration
```

### Standard function order inside each view file:

```
1. Imports
2. Constants / configuration
3. List functions
4. Create functions
5. Detail functions
6. Update functions
7. Delete functions
8. Specialized feature actions
9. AJAX / endpoint functions
```

---

## 7. Forms

Forms mirror models and views — same feature grouping:

```
inventory/models/item.py   ←→   inventory/forms/item.py   ←→   inventory/views/items.py
```

---

## 8. URL Naming

URL names must be `<feature>_<action>` — never vague:

```python
# GOOD
path('items/',              item_list,   name='item_list'),
path('items/create/',       item_create, name='item_create'),
path('items/<int:pk>/',     item_detail, name='item_detail'),
path('items/<int:pk>/edit/',item_update, name='item_update'),

# BAD
path('process/', handle, name='action'),
path('misc/',    do_it,  name='misc'),
```

---

## 9. Templates — Feature Subdirectory Rule

Templates must be organized into per-feature subdirectories:

```
inventory/templates/inventory/
├── base.html                  ← app-level base (stays at root)
├── items/
│   ├── list.html
│   ├── form.html
│   ├── detail.html
│   └── item_master_form.html
├── purchase/
│   └── order.html
├── stock/
│   └── list.html
├── reports/
│   └── index.html
└── dashboard/
    └── dashboard.html
```

**Two valid template types:**

| Type | When to use |
|---|---|
| Generic CRUD screen | Use `common/includes/profile_form.html` with `build_form_config()` |
| Specialized screen | Dedicated template for POS, KDS, dashboards, reports, maps |

---

## 10. Services — Reusable Business Logic Only

```
common/services/
├── accounting_service.py      ← journal entries, ledger postings
├── company_db_service.py      ← tenant DB connection helpers
├── data_fetcher.py            ← paginated, streamed SQL queries
├── inventory_service.py       ← stock movements, valuation
└── party_service.py           ← customer/vendor CRUD operations
```

**A service answers:** *"What reusable business operation is being performed?"*

**A service is NOT:** a dumping ground for random helpers.

When a vertical needs inventory or accounting:

```python
# GOOD
from common.services.inventory_service import UniversalInventoryService
from common.services.accounting_service import UniversalAccountingService
from common.services.party_service import save_party, load_party

# BAD — never create vertical-specific duplicates
# restaurant/inventory_service.py   ← forbidden
# laundry/accounting.py             ← forbidden
```

---

## 11. Utilities

```
common/utils/
├── document_utils.py          ← file naming, document handling
├── form_helpers.py            ← generic form-building helpers
├── profile_form_helpers.py    ← build_form_config(), build_hero_config(), field()
├── prefetch_utils.py          ← window.PAGE_PREFETCH URL builders
└── context_utils.py           ← module context (back_url, sidebar_template)
```

A utility must be a genuinely reusable **technical** operation — not a feature-specific business rule.

---

## 12. Static File Ownership

| Location | What goes there |
|---|---|
| `static/` | Global project-level assets |
| `common/static/common/` | Shared ERP design system (CSS, JS engines) |
| `inventory/static/inventory/` | Inventory-specific JS/CSS |
| `laundry/static/laundry/` | Laundry-specific JS/CSS |
| `restaurant/static/restaurant/` | Restaurant-specific JS/CSS |
| `financial/static/financial/` | Financial-specific JS/CSS |
| `reports/static/reports/` | Reports-specific JS/CSS |

Never copy shared JavaScript into multiple verticals.

---

## 13. `common/` — Shared App Organization

### Models (domain-split):
```
common/models/
├── __init__.py                ← re-exports all symbols
├── chart_of_code.py           ← universal key-value config store
├── company_information.py
├── customer.py                ← ChartOfAccounts + CustomerVendor DDL (MGROUP=36)
├── department.py
├── employee.py
├── filter_details.py
├── firm_master.py
├── group_setup.py
├── report_details.py
├── settings.py
├── supplier.py                ← vendor domain (MGROUP=37), re-exports customer DDL
└── user.py
```

### Views (feature-oriented):
```
common/views/
├── auth.py                    ← login, logout
├── company_info.py            ← company form CRUD
├── company_loader.py          ← tenant company loading
├── context_processors.py      ← Django context processors (registered in settings)
├── crud.py                    ← backward-compat shim → core.crud
├── customers.py               ← customer form (delegates to party_service)
├── dashboard.py               ← common dashboard
├── decorators.py              ← @login_required, @require_session_keys
├── department.py              ← department CRUD
├── documents.py               ← document load/save/serve
├── employee_import_config.py
├── filter_views.py            ← shared report filters
├── form_design.py             ← form layout designer
├── ftp_browse.py              ← FTP browser
├── global_settings.py         ← global settings CRUD
├── group_setup.py             ← group/hierarchy setup
├── import_excel.py            ← Excel import processing
├── party_import_config.py
├── party_master.py            ← UI config for customer/vendor forms + service re-exports
├── profile_form_helpers.py    ← backward-compat shim → common/utils/profile_form_helpers.py
├── report_style_views.py      ← report style CRUD
├── settings.py                ← theme, database settings views
└── vendors.py                 ← vendor form (delegates to party_service)
```

---

## 14. `core/` — Infrastructure Only

```
core/
├── management/commands/       ← create_superuser, migrate_logos, setup_database, switch_business
├── middleware/                ← audit_log, business_context, theme_loader
├── business_loader.py
├── context_processors.py
├── crud.py                    ← BaseCRUD — the ONE sanctioned CRUD abstraction
├── dbhelper.py
├── decorators.py              ← (infrastructure-level decorators)
├── exceptions.py
├── ftp.py
├── generic_urls.py
├── generic_views.py
├── mixins.py
├── signals.py
├── tasks.py
├── utils.py
└── validators.py
```

`core/` must not contain customer, inventory, laundry, restaurant, or accounting business tables.

---

## 15. `tools/` — Maintenance Scripts (Not Application Code)

```
tools/
├── maintenance/               ← fix_*, update_*, rebuild_*, add_*, cleanup_*
├── diagnostics/               ← debug_*, inspect_*, verify_*
├── data_migration/            ← one-time migration scripts
└── one_time/                  ← inject_*, test_* scripts
```

**Never import from `tools/` in application code.**

---

## 16. Root Directory — What Belongs There

```
ACRO-BIS/
├── manage.py
├── requirements.txt
├── README.md
├── package.json
├── package-lock.json
├── .env
├── .env.example
└── .gitignore
```

Fix scripts, temp files, debug utilities do **not** belong in the root. They go under `tools/`.

---

## 17. Prohibited — Never Create

| What | Why |
|---|---|
| `common2/`, `utils2/`, `new_common/` | No architecture loosening — use the existing folder |
| `restaurant/accounting.py` | Duplicate of `common/services/accounting_service.py` |
| `laundry/inventory_service.py` | Duplicate of `common/services/inventory_service.py` |
| Second `BaseCRUD` | `core/crud.py` is the one CRUD abstraction |
| Second tenant router | `common/db_router.py` is the one router |
| Second form engine | `profile_form.html` is the one CRUD form engine |
| Per-screen CSS for standard CRUD | Use the shared design system |
| Runtime `CREATE TABLE` | Use Django migrations |

---

## 18. Refactoring Workflow (Rule 39)

When reorganizing existing code:

1. Inspect the existing file
2. Identify all classes / functions / tables
3. Group by actual business responsibility
4. Identify all imports
5. Identify all URL references
6. Identify all template references
7. Propose the target structure
8. Move code — **do not rewrite business logic**
9. Update imports
10. Run `python manage.py check`
11. Verify affected screens load
12. Only then remove the obsolete file

---

## 19. Definition of Done

The architecture is correct when:

- [ ] Every business table has a clear model owner
- [ ] Every model file has a single clear domain
- [ ] Every view function belongs to a named feature
- [ ] No giant catch-all view, model, or form file exists
- [ ] Forms mirror model/view feature grouping
- [ ] URL names are `feature_action` format
- [ ] Templates are in `app/templates/app/feature/` subdirectories
- [ ] Services contain only reusable business operations
- [ ] `common/` remains shared (no vertical-specific logic)
- [ ] `core/` remains infrastructure (no business tables)
- [ ] Verticals are self-contained
- [ ] `reports/` and `api/` are presentation-only
- [ ] Tenant routing (`db_router.py`) is unchanged
- [ ] `BaseCRUD` (`core/crud.py`) remains the CRUD abstraction
- [ ] Profile form engine (`profile_form.html`) remains the CRUD form mechanism
- [ ] No `tools/` script is imported by application code
- [ ] No `.bak` files exist under a served static directory
- [ ] No duplicate business logic exists
- [ ] `python manage.py check` passes with 0 issues