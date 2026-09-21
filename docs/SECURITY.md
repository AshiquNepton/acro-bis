# ACRO-BIS Security & Tenant Isolation Policy

---

## 1. Multi-Tenant Database Isolation

- Every tenant operates on an isolated PostgreSQL database.
- Credentials (`db_host`, `db_name`, `db_user`, `db_password`) are extracted during authentication from the central `softwares` table and stored securely.
- `common/middleware/database_middleware.py` configures connections on a per-request basis using thread-local storage (`set_db_credentials`).
- **Zero cross-tenant data leakage**: No tenant has access to another tenant's credentials or database connection.

---

## 2. Authentication & Authorization

- All views are protected by the `@login_required` decorator in `common/views/decorators.py`.
- Custom middleware (`common/middleware/auth.py`) checks session integrity:
  - Validates `is_authenticated`, `custid`, and database credentials on every request.
  - Automatically redirects unauthenticated standard requests to the `/common/` login page.
  - Returns clean JSON `401 Unauthorized` responses for AJAX/fetch requests to prevent UI breakage.

---

## 3. Input Sanitization & SQL Injection Defense

- **No raw string interpolation into SQL queries.**
- All database operations in `core/crud.py` use parameterized queries (`%s` placeholders for PostgreSQL, `?` for SQLite).
- Strict whitelist column mapping via `FIELD_MAPPING` ensures frontend field inputs cannot inject arbitrary column names or SQL commands.

---

## 4. Credential Handling

- Tenant database credentials must **never** be exposed to the browser, HTML, JavaScript, API responses, logs, or client-visible error messages.
- Credentials must be stored and handled using the project's approved secure server-side session mechanism (see `common/middleware/database_middleware.py` and `common/middleware/auth.py`).
- **Never** hardcode tenant credentials in Python or JS files.
- **Never** log tenant passwords or full connection strings.

---

## 5. Error Information Disclosure Prevention

- Centralized error handlers in `errors/handlers.py` intercept `400`, `403`, `404`, and `500` status codes.
- Stack traces and sensitive connection parameters are logged locally to `logs/django.log` and are **never** exposed to the frontend.
- A missing table or schema mismatch is treated as an operational error (logged server-side, controlled JSON response) — never as a trigger to auto-create schema. See `DATABASE_GUIDE.md`.

---

## 6. API Layer Security (`api/`)

- API endpoints must use authentication/authorization appropriate to the endpoint — do not assume the same session-based auth as the HTML views transfers automatically without verification (use tokens/JWT where appropriate for stateless APIs).
- API code must respect tenant database isolation and must not bypass `DynamicDatabaseMiddleware`'s routing.
- API error responses follow the same standard JSON error contract as AJAX endpoints (§5) — no raw tracebacks, no connection strings.