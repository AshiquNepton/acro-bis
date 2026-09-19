# common/models/firm_master.py
"""
Model for the FirmMaster table.

This table lives in the COMPANY-SPECIFIC database
(e.g. acme_erp_7_2024_01_01_2024_12_31), NOT in the customer's main DB.

The Under field stores Organization.CompanyId as a plain integer FK
(no Django ForeignKey, because Organization lives in a different DB).
"""

import logging

from django.db import connections, OperationalError, ProgrammingError

logger = logging.getLogger(__name__)


_ENSURED_FIRM_TABLES = set()


def ensure_firm_master_table(db_alias: str, force: bool = False) -> bool:
    """
    Create the FirmMaster table in the given database alias if it does
    not already exist. Cached in memory so it executes at most once per process.

    Returns True on success, False on failure (non-fatal — callers log
    the error and continue so the rest of the form still loads).
    """
    if not force and db_alias in _ENSURED_FIRM_TABLES:
        return True

    ddl = """
        CREATE TABLE IF NOT EXISTS "FirmMaster" (
            "FirmID"   integer      NOT NULL,
            "FName"    varchar(50)  NULL,
            "Under"    integer      NOT NULL DEFAULT 0,
            "SubHead"  varchar(50)  NULL,
            "FStatus"  integer      NULL     DEFAULT 1,
            "Phone"    varchar(10)  NULL,
            "Address1" varchar(20)  NULL,
            "Address2" varchar(20)  NULL,
            "Address3" varchar(20)  NULL,
            CONSTRAINT "PK_FirmMaster" PRIMARY KEY ("FirmID")
        )
    """
    try:
        with connections[db_alias].cursor() as cur:
            cur.execute(ddl)
        _ENSURED_FIRM_TABLES.add(db_alias)
        logger.debug('ensure_firm_master_table: table ready in %s', db_alias)
        return True
    except (OperationalError, ProgrammingError) as exc:
        logger.error(
            'ensure_firm_master_table: could not create table in %s: %s',
            db_alias, exc
        )
        return False


# ─── Django model (managed=False — table created by ensure_ above) ───────────

from django.db import models


class FirmMaster(models.Model):
    """
    Department / Job / Project master.

    Lives in the company-specific database.
    Under stores the CompanyId from Organization (cross-DB reference).
    """

    FirmID   = models.IntegerField(primary_key=True, db_column='FirmID')
    FName    = models.CharField(max_length=50,  db_column='FName',    null=True, blank=True)
    Under    = models.IntegerField(              db_column='Under',    default=0)
    SubHead  = models.CharField(max_length=50,  db_column='SubHead',  null=True, blank=True)
    FStatus  = models.IntegerField(              db_column='FStatus',  null=True, blank=True, default=1)
    Phone    = models.CharField(max_length=10,  db_column='Phone',    null=True, blank=True)
    Address1 = models.CharField(max_length=20,  db_column='Address1', null=True, blank=True)
    Address2 = models.CharField(max_length=20,  db_column='Address2', null=True, blank=True)
    Address3 = models.CharField(max_length=20,  db_column='Address3', null=True, blank=True)

    class Meta:
        db_table = 'FirmMaster'
        managed  = False
        