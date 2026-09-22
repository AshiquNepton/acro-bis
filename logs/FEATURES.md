# Project Feature Change Log

All notable features, architecture consolidations, and module additions for **ACRO-BIS Multi-Tenant ERP** are documented in this file.

---

## [2026-09-22] - Selling Rates widget and Database Architecture Consolidation

### 1. Unified Selling Rates & Pricing
- **Stocks Table DDL Fixes** (`inventory/models/stock.py`):
  - Removed outdated `PurchasePrice` column as a distinct field; integrated as `Rate0` as the single source of truth for base cost, simplifying composite primary keys (`ItemID` only).
  - Added safe `ALTER` table migrations ensuring older deployed databases are upgraded automatically.
- **InventoryItems Table Fixes** (`inventory/models/item.py`):
  - Stripped `PurchasePrice`, `MRP`, `DRP`, `FDP` from table DDL. Pricing is exclusively managed via the Stocks module.
  - Added support for `PackingDetails` group hierarchy link.
- **Selling Rates Form Widget** (`inventory/views/item_master.py` & `item_master_form.html`):
  - Replaced flat inputs with a dynamic **Two-Way Rates Calculator** layout embedded directly in the profile form using existing project CSS classes (`pf-field-row`, `pf-field-ctl`, `pf-select`).
  - Added dropdowns for selecting the base calculation value (Landing Cost vs Purchase Price).
  - Dynamic javascript calculations: Users can enter either a `% markup` to calculate the final amount, or a `final amount` to back-calculate the `% markup`.

### 2. Form Rendering Compliance
- Strictly enforced adherence to native `profile_form.css` structure for inline layouts without introducing custom inline styles or new `.css` files, keeping the design robust across themes.

---

## [2026-09-12] - Inventory Master & Multi-Module Infrastructure Architecture

### 1. Inventory Module Implementation
- **Item Master View (`inventory/views/item_master.py`)**:
  - Declarative configuration via `build_item_master_form_config()`.
  - Seamless integration with `profile_form.html` universal form engine.
  - Zero inline or per-screen CSS duplication.
  - Two primary tabs: **General** (Identifiers, Codes/Tracking, Tax/Stock levels) and **UOM** (Base, Purchase, Sales, plus 5 configurable secondary units with conversion factors and barcodes).
- **Item Master Template (`inventory/templates/inventory/item_master_form.html`)**:
  - Reusable modal dialogs powered by the unified `UtilityModal` engine (`common/static/common/js/utilities_modal.js`).
  - **Item / Brand / Category 3-Split Modal**: Triggered on pressing `Enter` within the Item Name field; populates item name, brand, and category simultaneously.
  - **Bin Location Grid Modal**: Interactive row selection table returning comma-separated bin codes into the form.

### 2. Error Infrastructure (`errors/`)
- **Central Exception Hierarchy (`errors/exceptions.py`)**:
  - Base `ErpBaseException` with JSON serialization support.
  - `TenantDatabaseError`, `TenantConfigMissingError`, `RecordDuplicateError`, `RecordNotFoundError`, `ValidationError`.
  - Module-specific exceptions: `InventoryError`, `InsufficientStockError`, `InvalidUomConversionError`.
- **Global Error Handlers (`errors/handlers.py`)**:
  - `handler400`, `handler403`, `handler404`, `handler500`.
  - Automatic detection of AJAX/fetch requests returning JSON error responses rather than broken HTML views.
  - Handlers registered in `erp_project/urls.py`.

### 3. Daily Backup System (`scripts/backup_daily.ps1`)
- Automated daily backup mechanism saving to `backups/YYYY-MM-DD/`.
- Excludes heavy transient directories (`venv/`, `__pycache__/`, `.git/`, `staticfiles/`).
- Captures Git diff changes summary to `git_changes_summary.txt`.
- Implements automated retention policy (purges backups older than 14 days).
- Comprehensive operation logging to `logs/backup.log`.

### 4. Cross-Platform Windows & Terminal Compatibility
- Cleaned non-ASCII Unicode characters (box drawing and glyphs) across `settings/base.py` and `common/views/company_loader.py` preventing `charmap` encode exceptions on Windows `cp1252` terminals.
- Broadened `BUSINESS_TYPES` dictionary in `common/views/auth.py` to support Laundry (`1`), Restaurant (`2`), HRMS (`3`), Inventory (`4`), and Financial (`5`).

---

## [Initial Release] - Common Multi-Tenant ERP Architecture
- Session-based multi-tenant database routing via `DynamicDatabaseMiddleware` and `CustomerDatabaseRouter`.
- Central CRUD operations via `core/crud.py` (`BaseCRUD`).
- Common Masters: Company Information, Department/Job Master, Customers, Suppliers, Form Design customizer.
