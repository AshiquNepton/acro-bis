"""
errors/exceptions.py
====================
Centralized Exception Hierarchy for ACRO-BIS Multi-Tenant ERP.

Uniformly used across all modules:
  - common
  - inventory
  - laundry
  - restaurant
  - gym
  - logistics
  - financial
"""


class ErpBaseException(Exception):
    """Base exception for all domain exceptions in the ERP."""
    default_message = "An ERP application error occurred."
    status_code = 400

    def __init__(self, message=None, details=None):
        super().__init__(message or self.default_message)
        self.message = message or self.default_message
        self.details = details or {}

    def to_dict(self):
        return {
            'success': False,
            'error': self.message,
            'error_type': self.__class__.__name__,
            'details': self.details,
        }


# ── Database & Tenant Exceptions ─────────────────────────────────────────────

class TenantDatabaseError(ErpBaseException):
    """Raised when tenant customer database connection or query fails."""
    default_message = "Tenant database connection failed or is unreachable."
    status_code = 503


class TenantConfigMissingError(ErpBaseException):
    """Raised when tenant configuration or session credentials are not found."""
    default_message = "Tenant session credentials or database settings are missing."
    status_code = 401


# ── Validation & Integrity Exceptions ────────────────────────────────────────

class RecordDuplicateError(ErpBaseException):
    """Raised when an entity violates uniqueness constraints (e.g. duplicate code/name)."""
    default_message = "A record with this identifier or name already exists."
    status_code = 409


class RecordNotFoundError(ErpBaseException):
    """Raised when a requested record does not exist in the tenant database."""
    default_message = "The requested record was not found."
    status_code = 404


class ValidationError(ErpBaseException):
    """Raised on form or payload validation failure."""
    default_message = "Validation error occurred on the submitted data."
    status_code = 422


# ── Module-Specific Exceptions (Extensible for all business types) ───────────

class InventoryError(ErpBaseException):
    """Base exception for inventory operations."""
    default_message = "An inventory processing error occurred."


class InsufficientStockError(InventoryError):
    """Raised when an outbound movement exceeds available stock."""
    default_message = "Insufficient stock available for this transaction."
    status_code = 400


class InvalidUomConversionError(InventoryError):
    """Raised when unit of measurement conversion factor is invalid or zero."""
    default_message = "Invalid unit of measurement conversion factor specified."
    status_code = 400

class SchemaError(TenantDatabaseError):
    """Raised when a required database table or schema object is missing."""
    default_message = 'Required database schema is missing. Please run pending migrations.'
    status_code = 500

