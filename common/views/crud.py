"""
Backward-compatibility shim for common.views.crud.

Per ACRO-BIS ARCHITECTURE.md (Section 3, Tier 1: Shared Platform) and
CODING_STANDARDS.md (Golden Rule 1: Never Duplicate Code), all universal
CRUD logic is centralized in core.crud.

This module re-exports everything from core.crud so any legacy or
existing references (and tests) continue to resolve seamlessly.
"""

from core.crud import *  # noqa: F401, F403
import core.crud as _core_crud

# Explicitly re-export private module-level helpers and symbols
# used by existing unit tests and callers:
BaseCRUD = _core_crud.BaseCRUD
_coerce = _core_crud._coerce
_safe = _core_crud._safe
_parse_field_map = _core_crud._parse_field_map
_resolve_length_errors = _core_crud._resolve_length_errors
_is_identity_column = _core_crud._is_identity_column
safe_atomic = _core_crud.safe_atomic
connections = _core_crud.connections
logger = _core_crud.logger