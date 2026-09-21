# ACRO-BIS — Multi-Tenant Enterprise ERP Platform

A modular, scalable, multi-tenant Django ERP supporting multiple business verticals under a single unified architecture.

| Software ID | Vertical |
|:-----------:|----------|
| 1 | Laundry & Dry Cleaning |
| 2 | Restaurant & Point of Sale (POS) |
| 3 | HRMS & Workforce Management |
| 4 | Inventory & Supply Chain |
| 5 | Financial & General Ledger |
| 6 | Logistics & Fleet Management *(upcoming)* |
| 7 | Gym & Fitness Management *(upcoming)* |

---

## Repository Layout

```
ACRO-BIS/
│
├── api/                        # External API presentation layer
│   ├── serializers/            #   common/, laundry/, restaurant/
│   ├── views/                  #   common/, laundry/, restaurant/
│   └── urls.py
│
├── common/                     # Shared ERP functionality (cross-vertical)
│   ├── db_backend/             #   Custom PostgreSQL backend
│   ├── forms/                  #   auth.py, customer.py, supplier.py, settings.py
│   ├── middleware/             #   auth.py, database_middleware.py, business_guard.py
│   ├── models/                 #   customer.py, supplier.py, chart_of_code.py,
│   │                           #   company_information.py, employee.py, department.py,
│   │                           #   firm_master.py, group_setup.py, settings.py, user.py
│   ├── services/               #   accounting_service.py, company_db_service.py,
│   │                           #   data_fetcher.py, inventory_service.py, party_service.py
│   ├── static/common/          #   Global CSS design system + shared JS engines
│   ├── templates/common/       #   base.html, profile_form.html, layout.html, sidebar.html
│   ├── utils/                  #   document_utils.py, form_helpers.py,
│   │                           #   profile_form_helpers.py, prefetch_utils.py, context_utils.py
│   ├── views/                  #   auth.py, customers.py, vendors.py, dashboard.py,
│   │                           #   company_info.py, department.py, settings.py, documents.py,
│   │                           #   party_master.py, context_processors.py, decorators.py, …
│   ├── db_router.py            #   Multi-tenant DB routing
│   └── urls.py
│
├── config/                     # JSON configuration files
│
├── core/                       # Infrastructure layer (no business logic)
│   ├── management/commands/    #   create_superuser, migrate_logos, setup_database, switch_business
│   ├── middleware/             #   audit_log.py, business_context.py, theme_loader.py
│   ├── crud.py                 #   BaseCRUD — the ONE sanctioned CRUD abstraction
│   ├── dbhelper.py             #   Low-level DB utilities
│   ├── exceptions.py           #   Core exception types
│   ├── validators.py
│   └── ftp.py
│
├── docs/                       # Project documentation (you are here)
│   ├── ARCHITECTURE.md
│   ├── CODING_STANDARDS.md
│   ├── DATABASE_GUIDE.md
│   ├── DEVELOPMENT_GUIDE.md
│   └── SECURITY.md
│
├── erp_project/                # Django project root (settings, root urls, wsgi)
│   └── settings/               #   base.py, local.py
│
├── errors/                     # Central exception hierarchy & HTTP error handlers
│
├── financial/                  # Financial & General Ledger vertical
│   ├── models/                 #   account.py, journal.py, ledger.py, voucher.py
│   ├── forms/                  #   account.py, voucher.py
│   ├── views/                  #   accounts.py, dashboard.py, reports.py, statements.py, vouchers.py
│   ├── templates/financial/    #   accounts/, vouchers/, statements/, reports/, dashboard/
│   └── static/financial/
│
├── inventory/                  # Inventory & Supply Chain vertical
│   ├── models/                 #   category.py, item.py, purchase.py, stock.py, warehouse.py
│   ├── forms/                  #   item.py, purchase.py, stock.py
│   ├── views/                  #   dashboard.py, items.py, item_master.py, purchase.py,
│   │                           #   stock.py, reports.py, import_view.py, import_config.py
│   ├── templates/inventory/    #   items/, purchase/, stock/, reports/, dashboard/
│   └── static/inventory/
│
├── laundry/                    # Laundry & Dry Cleaning vertical
│   ├── models/                 #   delivery.py, garment.py, invoice.py, order.py, pricing.py, service.py
│   ├── forms/                  #   order.py, pricing.py, service.py
│   ├── views/                  #   dashboard.py, delivery.py, orders.py, pricing.py, reports.py, services.py
│   ├── templates/laundry/      #   orders/, delivery/, pricing/, services/, reports/, dashboard/
│   └── static/laundry/
│
├── locale/                     # i18n translation files
│
├── logs/                       # Application logs & feature changelog
│   └── FEATURES.md
│
├── reports/                    # Cross-vertical reporting layer (read-only)
│   ├── utils/                  #   excel_generator.py, pdf_generator.py
│   ├── views/                  #   custom_reports.py, dashboard.py, financial_reports.py,
│   │                           #   inventory_reports.py, party_reports.py, sales_reports.py
│   ├── templates/reports/
│   └── static/reports/
│
├── restaurant/                 # Restaurant & POS vertical
│   ├── models/                 #   booking.py, category.py, kot.py, menu.py, order.py, recipe.py, table.py
│   ├── forms/                  #   booking.py, menu.py, order.py, table.py
│   ├── views/                  #   dashboard.py, kitchen.py, menu.py, orders.py, pos.py, reports.py, tables.py
│   ├── templates/restaurant/   #   kitchen/, menu/, orders/, pos/, tables/, reports/, dashboard/
│   └── static/restaurant/
│
├── scripts/                    # Deployment & backup scripts (ops use only)
│   ├── backup_daily.ps1
│   ├── deploy.sh
│   └── migrate.sh
│
├── static/                     # Global static assets (served at project level)
│   ├── css/
│   └── js/
│
├── templates/                  # Global templates (404.html, 500.html, base.html)
│
├── tests/                      # Test suite
│   ├── fixtures/test_data.json
│   ├── test_common.py
│   ├── test_core.py
│   ├── test_laundry.py
│   └── test_restaurant.py
│
├── tools/                      # Maintenance & diagnostic scripts (not imported by app)
│   ├── maintenance/            #   fix_*, update_*, rebuild_*, cleanup_* scripts
│   ├── diagnostics/            #   debug_*, inspect_*, verify_* scripts
│   ├── data_migration/         #   one-time migration scripts
│   └── one_time/               #   inject_*, test_* scripts
│
├── manage.py
├── requirements.txt
├── package.json
├── .env.example
├── .gitignore
└── README.md
```

---

## Core Rules (Summary)

1. **One feature, one owner** — every table → model → form → view → URL → template → static must have a clear, predictable home. See `docs/ARCHITECTURE.md`.
2. **No duplicate abstractions** — one CRUD engine (`core/crud.py`), one tenant router (`common/db_router.py`), one form engine (`profile_form.html`).
3. **Common vs. Vertical boundary** — `common/` and `core/` must never import from a vertical. Verticals must never import each other.
4. **No runtime schema changes** — `CREATE`/`ALTER`/`DROP` belongs in migrations, not views or services. See `docs/DATABASE_GUIDE.md`.
5. **No inline CSS / per-screen CSS** — CRUD screens use the shared design system (`profile_form.css`, `colors.css`).
6. **No credentials in code** — read from `.env` or session. Never log passwords or connection strings.

---

## Quick Start

```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate          # Windows
source venv/bin/activate         # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Check project integrity
python manage.py check

# Start development server
python manage.py runserver 8000
```

---

## Daily Backup

```powershell
powershell -ExecutionPolicy Bypass -File "scripts\backup_daily.ps1"
```

Backups are saved to `backups/YYYY-MM-DD/` with Git diff tracking.

---

## Documentation

| Document | Purpose |
|---|---|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Module/model/view/URL/template organization rules |
| [CODING_STANDARDS.md](docs/CODING_STANDARDS.md) | Naming, style, docstrings, form engine usage |
| [DATABASE_GUIDE.md](docs/DATABASE_GUIDE.md) | Migration-only schema rule, multi-tenant considerations |
| [DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md) | Where code belongs, recipe for adding new features |
| [SECURITY.md](docs/SECURITY.md) | Tenant isolation, auth, credential handling |
| [FEATURES.md](logs/FEATURES.md) | Feature log & change history |
