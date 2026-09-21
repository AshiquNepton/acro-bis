"""
common/models/supplier.py

Defines the Supplier / Vendor domain — backed by the same ChartOfAccounts +
CustomerVendor tables as customers, distinguished by MGroup.

This system uses raw SQL against a multi-tenant PostgreSQL database rather than
Django ORM migrations, so this module re-exports the shared DDL and field
constants from customer.py along with the Vendor-specific MGroup constant.

Tables
──────
  ChartOfAccounts  — master account record (shared with customers, via MGroup)
  CustomerVendor   — extended party details (address, contacts, financials)

MGroup value for vendors: 37
"""

# ── MGroup constant ─────────────────────────────────────────────────────────
VENDOR_MGROUP = 37

# ── Re-export shared DDL and field constants from customer domain ─────────
# The underlying tables are identical for both customers and vendors;
# only the MGroup column distinguishes the two party types.
from common.models.customer import (   # noqa: E402, F401
    CHART_OF_ACCOUNTS_DDL,
    CUSTOMER_VENDOR_DDL,
    CUSTOMER_VENDOR_FIELDS,
)
