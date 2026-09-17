# ACRO-BIS Multi-Tenant ERP Architecture

## 1. Multi-Tenant Philosophy
ACRO-BIS is built as a scalable, multi-tenant enterprise system capable of hosting multiple business verticals under a unified architecture:
- **HRMS** (`business_type = 3`)
- **Inventory & Supply Chain** (`business_type = 4`)
- **Laundry & Dry Cleaning** (`business_type = 1`)
- **Restaurant & POS** (`business_type = 2`)
- **Financial & General Ledger** (`business_type = 5`)
- **Logistics & Warehousing** (Upcoming)
- **Gym & Fitness Management** (Upcoming)

---

## 2. Zero Duplication Principles

### A. Zero Custom CSS Per Screen
- **Rule**: Never create custom CSS files for individual forms or screens.
- All visual components, themes, and inputs inherit strictly from:
  - `common/static/common/css/colors.css` (global CSS variables)
  - `common/static/common/css/profile_form.css` (form engine styling)
  - `common/static/common/css/utilities_modal.css` (modal system)
  - `common/static/common/css/tables.css` (data grids)

### B. Declarative Python Views
- Screens are defined entirely in Python views using `build_form_config()`, `build_hero_config()`, and `field()` from `common/views/profile_form_helpers.py`.
- HTML templates remain paper-thin wrappers:
  ```html
  {% extends 'common/base.html' %}
  {% block content %}
  {% include 'common/includes/profile_form.html' with fc=form_config %}
  {% endblock %}
  ```

### C. Common Backend & Database Abstraction
- All database operations route through `core/crud.py` (`BaseCRUD`).
- No raw, repetitive SQL queries scattered across views.
- Dynamic multi-tenant connection swapping is managed once via `common/middleware/database_middleware.py` (`DynamicDatabaseMiddleware`).

---

## 3. Directory Blueprint & Boundary Rules

To prevent architectural chaos as the project scales to hundreds of models and multiple verticals (Laundry, Restaurant, Inventory, Gym, Logistics), follow the strict **Separation of Concerns**:

### Tier 1: Shared Framework & Core (`common/`, `core/`, `errors/`)
*Contains ZERO business-vertical logic. These are untouchable by domain apps.*
- `core/`: Universal database CRUD abstraction (`BaseCRUD`), FTP client, multi-tenant DB helpers.
- `common/`: 
  - Central Auth & Session Middleware (`AuthenticationMiddleware`, `DynamicDatabaseMiddleware`).
  - Base Layout & Global Navigation (`common/templates/common/base.html`, `profile_form.html`).
  - Global CSS Design System (`common/static/common/css/colors.css`, `profile_form.css`, `utilities_modal.css`).
  - Global JS Engines (`profile_form.js`, `utilities_modal.js`).
  - Shared Enterprise Masters (`Organization`/Company Information, `FirmMaster`/Department/Job Master, Users/Customers).
  - High-Performance Query Service (`common/services/data_fetcher.py`).
- `errors/`: Centralized domain exceptions & global AJAX/JSON error handlers.

### Tier 2: Business Verticals (`inventory/`, `laundry/`, `restaurant/`, `gym/`, `logistics/`, etc.)
*Each business vertical must be fully self-contained.*
- **Rules**:
  1. A vertical only contains its own domain models, views, forms, and URLs (e.g. `inventory/views/item_master.py`).
  2. A vertical **MUST NOT** import private models or views from another vertical (e.g. `inventory` must not import from `laundry`).
  3. If two verticals need the same functionality (e.g. barcode generation, tax rules, currency formatting), it **MUST** be placed in `common/` or `core/`.
  4. Vertical templates must only contain the thin `profile_form.html` inclusion wrapper—**NEVER** inline `<style>` tags or per-screen CSS files.

```
ACRO-BIS/
├── erp_project/        # Root Django configuration & routing
│
├── [TIER 1: COMMON PLATFORM]
│   ├── core/           # Universal CRUD (BaseCRUD), FTP utilities, DB helpers
│   ├── common/         # Auth, base layouts, masters, global CSS/JS, DataFetcher
│   └── errors/         # Central exception hierarchy & global 400/403/404/500 handlers
│
├── [TIER 2: BUSINESS VERTICALS]
│   ├── inventory/      # Stock, Items, UOM conversions, Warehouses
│   ├── laundry/        # Laundry orders, garments, washing cycles
│   ├── restaurant/     # POS, tables, kitchen display, recipes
│   ├── financial/      # Chart of Accounts, General Ledger, Vouchers
│   ├── gym/            # Memberships, biometric check-in, trainers (Upcoming)
│   └── logistics/      # Fleet, dispatches, waybills, trips (Upcoming)
│
└── [TIER 3: SYSTEM INFRASTRUCTURE]
    ├── docs/           # System design & developer guidelines
    ├── logs/           # Application, backup, and feature logs
    ├── backups/        # Daily automated project backups (backups/YYYY-MM-DD)
    └── scripts/        # PowerShell & Bash deployment/backup scripts
```

---

## 5. Universal Cross-Module Services Pattern

When any business vertical (Laundry, Restaurant POS, Logistics, Gym) needs stock tracking or financial posting, it **never duplicates inventory or accounting tables**. Instead, it directly calls the shared services located in `common/services/`:

### A. Universal Inventory Service (`common.services.inventory_service.UniversalInventoryService`)
- **Stock Movements**:
  ```python
  from common.services.inventory_service import UniversalInventoryService

  # Laundry detergent consumption:
  UniversalInventoryService.record_movement('DET-01', 'OUT', 2.5, 'ORD-1002', 'laundry')

  # Restaurant / POS sale:
  UniversalInventoryService.record_movement('COKE-CAN', 'OUT', 1, 'BILL-5401', 'restaurant')

  # Gym supplement / drink purchase:
  UniversalInventoryService.record_movement('PROT-SHAKE', 'OUT', 1, 'POS-902', 'gym')
  ```
- **Stock Availability Checking**:
  ```python
  available = UniversalInventoryService.check_availability('TIRE-R16', required_qty=4)
  ```

### B. Universal Accounting Service (`common.services.accounting_service.UniversalAccountingService`)
- **Double-Entry Journal Postings**:
  ```python
  from common.services.accounting_service import UniversalAccountingService

  UniversalAccountingService.post_journal_entry(
      voucher_type='SALES',
      reference_no='BILL-5401',
      narration='Restaurant Dine-In POS Bill #5401',
      source_module='restaurant',
      entries=[
          {'account_code': '1010-CASH', 'debit': 150.00, 'credit': 0},
          {'account_code': '4010-FOOD-REV', 'debit': 0, 'credit': 150.00},
      ]
  )
  ```

### C. Unified Reports Engine (`reports/` & `DataFetcher`)
All reports across all modules use `DataFetcher.stream_large_dataset()` to query and export records with zero memory spikes or delays.


