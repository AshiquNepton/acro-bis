# Tools

This directory contains maintenance, diagnostic, migration, and one-time scripts.
**Do not import these from application code.**

| Directory | Purpose |
|---|---|
| `maintenance/` | Recurring maintenance scripts (`fix_*`, `update_*`, `rebuild_*`, `add_*`, `cleanup_*`) |
| `diagnostics/` | Database and system diagnostic scripts (`debug_*`, `inspect_*`, `verify_*`) |
| `data_migration/` | One-time data migration scripts |
| `one_time/` | One-time injection or setup scripts (`inject_*`, `test_*`) |
