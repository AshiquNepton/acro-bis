# ACRO-BIS Multi-Tenant Enterprise ERP Platform

A modular, scalable, multi-tenant Django ERP platform engineered to support multiple business verticals under a unified architectural foundation:
- **Inventory & Supply Chain** (`software_id = 4`)
- **HRMS & Workforce Management** (`software_id = 3`)
- **Laundry & Dry Cleaning** (`software_id = 1`)
- **Restaurant & Point of Sale (POS)** (`software_id = 2`)
- **Financial & General Ledger** (`software_id = 5`)
- **Logistics & Fleet Management** (`software_id = 6`, Upcoming)
- **Gym & Fitness Management** (`software_id = 7`, Upcoming)

---

## Architecture & Code Organization Policy

To ensure scalability and maintainability, the project strictly enforces a **Separation of Concerns**:

```
ACRO-BIS/
├── erp_project/                    # Root Django configuration, WSGI/ASGI, URLs
│
├── [SHARED COMMON PLATFORM]        # Reusable core (Domain-Agnostic)
│   ├── core/                       # Universal CRUD engine (BaseCRUD), FTP manager, DB helpers
│   ├── common/                     # Global Auth, Session middleware, base layouts, masters, global CSS/JS
│   │   ├── middleware/             # DynamicDatabaseMiddleware, AuthenticationMiddleware
│   │   ├── services/               # DataFetcher, UniversalInventoryService, UniversalAccountingService
│   │   ├── static/common/          # Global CSS Design System (colors.css, profile_form.css) & JS engines
│   │   └── templates/common/       # base.html, profile_form.html universal engine
│   └── errors/                     # Central exception hierarchy & global 400/403/404/500 handlers
│
├── [BUSINESS VERTICAL MODULES]     # Independent domain apps (Self-Contained)
│   ├── inventory/                  # Items, Stock movements, Warehouses, UOM conversions
│   ├── laundry/                    # Laundry orders, garments, washing cycles
│   ├── restaurant/                 # POS, tables, kitchen display, recipes
│   ├── financial/                  # Chart of Accounts, General Ledger, Vouchers
│   ├── reports/                    # Universal reporting engine using DataFetcher
│   ├── gym/                        # Memberships, biometric check-in (Upcoming)
│   └── logistics/                  # Fleet, dispatches, waybills, trips (Upcoming)
│
└── [OPERATIONS & INFRASTRUCTURE]
    ├── docs/                       # ARCHITECTURE.md, CODING_STANDARDS.md, DEVELOPMENT_GUIDE.md, SECURITY.md
    ├── logs/                       # Application, backup, and feature logs
    ├── backups/                    # Automated daily backups (backups/YYYY-MM-DD)
    └── scripts/                    # PowerShell & Bash deployment/backup scripts
```

---

## Core Rules for All Developers

1. **Zero CSS Duplication**:
   - Never write per-screen CSS files or inline `<style>` blocks.
   - All forms inherit from `common/static/common/css/colors.css` and `profile_form.css`.
2. **Common vs. Vertical Boundary**:
   - If a feature is used across 2 or more verticals (e.g. inventory consumption, double-entry accounting, paginated data fetching), it **must** be placed in `common/services/`.
   - Vertical modules must **never** import each other directly.
3. **High-Performance Data Fetching (`DataFetcher`)**:
   - Always query large tables via `common.services.data_fetcher.DataFetcher` to avoid memory spikes and eliminate query delay.
4. **Universal Form Engine (`profile_form.html`)**:
   - Every form screen is declared via Python dictionary configuration (`build_form_config()`) and rendered with the paper-thin `profile_form.html` inclusion.
5. **Simple & Beginner-Friendly Python**:
   - Prioritize clear, explicit, readable code and descriptive variable names over clever one-liners or complex metaclasses so new collaborators can understand and contribute immediately. Include clear comments and docstrings.

---

## Quick Start Guide

### 1. Requirements & Environment
- Python 3.10+
- PostgreSQL (Customer/Tenant Databases)

### 2. Setup
```bash
# Clone and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run system checks
python manage.py check

# Start development server
python manage.py runserver 8000
```

### 3. Automated Daily Backup
To run a project backup with Git diff tracking (saves to `E:\ACRO_DEV_BACKUP\YYYY-MM-DD`):
```powershell
powershell -ExecutionPolicy Bypass -File "scripts\backup_daily.ps1"
```

---

## Documentation Index
- [Architecture Blueprint](docs/ARCHITECTURE.md)
- [Coding Standards & Zero-CSS Policy](docs/CODING_STANDARDS.md)
- [Developer & Modular Restructuring Guide](docs/DEVELOPMENT_GUIDE.md)
- [Security & Tenant Isolation Policy](docs/SECURITY.md)
- [Feature Log & Change History](logs/FEATURES.md)
