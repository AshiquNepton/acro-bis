# common/services/company_db_service.py
"""
Handles all PostgreSQL database-creation logic for company records.

Responsibilities
────────────────
1. Build a deterministic DB name from customer_db + company_id + period.
2. CREATE DATABASE on the PostgreSQL server (using admin creds from .env).
3. Store the generated DbName back onto the Organization row.
4. When "Set as Default" is ticked, update the session so all subsequent
   queries in this request cycle use the new company DB.

Admin credentials
─────────────────
CREATE DATABASE must run outside a transaction and requires a superuser or a
user with CREATEDB privilege.  We read those from .env:

    ADMIN_DB_USER=postgres
    ADMIN_DB_PASSWORD=secret

The host / port are the same as the customer's current connection (read from
the session that the middleware already populated).
"""

import re
import logging
import os

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

from common.db_backend.base import set_db_credentials

logger = logging.getLogger(__name__)

# ── Load .env once at import time ─────────────────────────────────────────────
_env_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'
)
load_dotenv(_env_path)


def _admin_credentials() -> dict:
    """
    Return the superuser credentials used to run CREATE DATABASE.
    Falls back to the regular DB_USER if ADMIN_DB_USER is not set.
    """
    return {
        'user'    : os.getenv('ADMIN_DB_USER')     or os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('ADMIN_DB_PASSWORD') or os.getenv('DB_PASSWORD', ''),
    }


def _sanitize_identifier(value: str) -> str:
    """
    Strip characters that are illegal in PostgreSQL identifiers.
    Keeps alphanumerics and underscores; replaces everything else with '_'.
    Also lower-cases to avoid case-sensitivity surprises.
    """
    value = value.lower()
    value = re.sub(r'[^a-z0-9_]', '_', value)
    # Collapse multiple consecutive underscores
    value = re.sub(r'_+', '_', value)
    return value.strip('_')


def build_company_db_name(customer_db_name: str, company_id: int,
                           period_from, period_to) -> str:
    """
    Produce a deterministic, collision-free PostgreSQL database name.

    Pattern:  {customer_db}_{company_id}_{period_from}_{period_to}
    Example:  acme_erp_7_2024_01_01_2024_12_31

    The name is guaranteed to:
      • contain only [a-z0-9_]
      • start with a letter or underscore (PostgreSQL requirement)
      • be ≤ 63 characters (PostgreSQL identifier limit)
    """
    base   = _sanitize_identifier(str(customer_db_name))
    cid    = str(company_id)
    pf     = _sanitize_identifier(str(period_from))   # date → '2024_01_01'
    pt     = _sanitize_identifier(str(period_to))

    name = f"{base}_{cid}_{pf}_{pt}"

    # Ensure it starts with a letter
    if name and name[0].isdigit():
        name = f"db_{name}"

    # Truncate to 63 chars (PostgreSQL limit)
    if len(name) > 63:
        # Keep the suffix (company_id + periods) which is the unique part
        suffix = f"_{cid}_{pf}_{pt}"
        max_base = 63 - len(suffix)
        name = base[:max_base] + suffix

    return name


def _db_exists(cursor, db_name: str) -> bool:
    """Return True if a PostgreSQL database with this name already exists."""
    cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        [db_name]
    )
    return cursor.fetchone() is not None


def create_company_database(request, company_id: int,
                             period_from, period_to) -> str:
    """
    Create a PostgreSQL database for the given company + period combination.

    Steps
    ─────
    1. Derive DB name from session's customer_db_name + company_id + period.
    2. Open an AUTOCOMMIT connection with admin credentials (CREATE DATABASE
       cannot run inside a transaction).
    3. Skip creation if the DB already exists (idempotent).
    4. Return the DB name so the caller can store it on the Organization row.

    Raises
    ──────
    RuntimeError  – if session credentials are missing or the CREATE fails.
    """
    db_host = request.session.get('db_host', '')
    db_port = request.session.get('db_port', '5432') or '5432'
    db_name = request.session.get('db_name', '')

    if not all([db_host, db_name]):
        raise RuntimeError(
            "Session is missing db_host / db_name — cannot create company database."
        )

    new_db_name = build_company_db_name(db_name, company_id, period_from, period_to)
    admin_creds = _admin_credentials()

    conn = None
    try:
        conn = psycopg2.connect(
            host    =db_host,
            port    =int(db_port),
            dbname  ='postgres',      # Connect to maintenance DB
            user    =admin_creds['user'],
            password=admin_creds['password'],
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        with conn.cursor() as cur:
            if _db_exists(cur, new_db_name):
                logger.info(
                    "company_db_service: DB '%s' already exists — skipping CREATE.",
                    new_db_name
                )
            else:
                # Safe: name was sanitized to [a-z0-9_] so no SQL-injection risk.
                cur.execute(f'CREATE DATABASE "{new_db_name}"')
                logger.info(
                    "company_db_service: Created database '%s' for company_id=%s.",
                    new_db_name, company_id
                )

    except Exception as exc:
        logger.error(
            "company_db_service: Failed to create DB '%s': %s",
            new_db_name, exc, exc_info=True
        )
        raise RuntimeError(f"Could not create company database '{new_db_name}': {exc}") from exc
    finally:
        if conn:
            conn.close()

    return new_db_name


def switch_session_to_company_db(request, new_db_name: str) -> None:
    """
    Update the session so that all subsequent queries in this session use the
    specified company database.

    We reuse the same host / port / user / password that are already in the
    session — only the db_name changes.  We also call set_db_credentials() so
    the *current* request's thread-locals are updated immediately (the
    middleware already ran for this request, so we must patch thread-locals
    manually here).
    """
    db_host     = request.session.get('db_host', '')
    db_port     = request.session.get('db_port', '5432') or '5432'
    db_user     = request.session.get('db_user', '')
    db_password = request.session.get('db_password', '')

    # Persist in session (next requests pick it up via middleware)
    request.session['db_name'] = new_db_name
    request.session.modified   = True

    # Patch current request's thread-locals immediately
    set_db_credentials(db_host, db_port, new_db_name, db_user, db_password)

    # Close any cached connection so the next query opens fresh
    try:
        from django.db import connections
        connections['customer_db'].close()
    except Exception:
        pass

    logger.info(
        "company_db_service: Session switched to company DB '%s'.", new_db_name
    )