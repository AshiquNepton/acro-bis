# ACRO-BIS Security & Tenant Isolation Policy

## 1. Multi-Tenant Database Isolation
- Every tenant operates on an isolated PostgreSQL database.
- Credentials (`db_host`, `db_name`, `db_user`, `db_password`) are extracted during authentication from the central `softwares` table and stored strictly in the encrypted session.
- `common/middleware/database_middleware.py` configures connections on a per-request basis using thread-local storage (`set_db_credentials`).
- **Zero cross-tenant data leakage**: No tenant has access to another tenant's credentials or database connection.

---

## 2. Authentication & Authorization
- All views are protected by the `@login_required` decorator in `common/views/decorators.py`.
- Custom middleware (`common/middleware/auth.py`) checks session integrity:
  - Validates `is_authenticated`, `custid`, and database credentials on every request.
  - Automatically redirects standard requests to `/common/` login.
  - Returns clean JSON `401 Unauthorized` responses for AJAX/fetch requests to prevent UI breakage.

---

## 3. Input Sanitization & SQL Injection Defense
- No raw string interpolation into SQL queries.
- All database operations in `core/crud.py` use parameterized queries (`%s` placeholders for PostgreSQL, `?` for SQLite).
- Strict whitelist column mapping via `FIELD_MAPPING` ensures frontend field inputs cannot inject arbitrary column names or commands.

---

## 4. Error Information Disclosure Prevention
- Centralized error handlers in `errors/handlers.py` intercept `400`, `403`, `404`, and `500` status codes.
- Stack traces and sensitive connection parameters are logged locally to `logs/django.log` and are never exposed to the frontend.
