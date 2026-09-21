# hrms/models/employee.py
"""
Employees table definition for customer_db (PostgreSQL).
No Django ORM migrations — created via raw SQL by ensure_employees_table().

Columns removed vs original DDL:
  - AdmNo     : was never in FIELD_MAP, never shown in any form
  - EmpStatus : was never in FIELD_MAP, never shown in any form

Columns kept even though browse_btn was removed from the UI:
  - ContractFPath, FileFolder, HFDocument, HBDocument
    These store FTP paths uploaded through the Documents menu modal.
    Removing them would lose document references already in the DB.

New columns (2025):
  - MobApp        INTEGER  DEFAULT 0   — 1=Yes, 0=No  (Mobile App access)
  - AttendanceLoc INTEGER  DEFAULT 0   — 1=Fixed, 0=Flexible
  - AppPass       VARCHAR(50)          — MD5-hashed mobile app password
  - LocID         INTEGER              — FK → AttendanceLocations.LocID
                                         (only relevant when AttendanceLoc=1)
"""

import logging
from django.db import connections
from django.db.utils import ProgrammingError, OperationalError

logger = logging.getLogger(__name__)


CREATE_EMPLOYEES_SQL = """
CREATE TABLE IF NOT EXISTS "Employees" (

    -- ── Identity / Registration ──────────────────────────────────────────
    "RegNo"             VARCHAR(10)     NOT NULL,

    -- ── Name ────────────────────────────────────────────────────────────
    "EmpName"           VARCHAR(100),
    "EmpNameArabic"     VARCHAR(120),

    -- ── Personal ────────────────────────────────────────────────────────
    "DOB"               DATE,
    "Gender"            INTEGER,
    "MaritalStatus"     INTEGER,
    "BloodGroup"        INTEGER,
    "ReportTo"          INTEGER,
    "Nationality"       INTEGER,
    "Religion"          INTEGER,
    "Qualification"     INTEGER,
    "Accomadation"      INTEGER,
    "Experiance"        INTEGER,

    -- ── Contact ─────────────────────────────────────────────────────────
    "PermanentAddress"  VARCHAR(300),
    "Phone"             VARCHAR(15),
    "Mobile"            VARCHAR(15),
    "Contact"           VARCHAR(60),
    "Email"             VARCHAR(200),

    -- ── Organisation ────────────────────────────────────────────────────
    "Department"        INTEGER,
    "Desig"             INTEGER,
    "GroupID"           INTEGER,
    "Active"            INTEGER,
    "ActualJob"         INTEGER,
    "CurrentProj"       INTEGER,
    "EmployeeType"      INTEGER,

    -- ── Bank ────────────────────────────────────────────────────────────
    "BankName"          INTEGER,
    "BAccNO"            VARCHAR(50),

    -- ── Passport / RP ───────────────────────────────────────────────────
    "PasportNo"         VARCHAR(50),
    "PassportWith"      INTEGER,
    "PPIssueDate"       DATE,
    "PPExpiryDate"      DATE,
    "RPNo"              VARCHAR(50),
    "RPExpiryDate"      DATE,
    "SponsorID"         VARCHAR(20),
    "Sponsor"           VARCHAR(100),
    "DOJ"               DATE,
    "RetirementDate"    DATE,

    -- ── Licence / Medical / Insurance / Health / Contract ───────────────
    "LisenceNo"         VARCHAR(20),
    "LExpiryDate"       DATE,
    "MedicalCard"       VARCHAR(20),
    "MCExpiry"          DATE,
    "Insurance"         VARCHAR(20),
    "INExpiry"          DATE,
    "HealthCard"        VARCHAR(20),
    "HCExpiry"          DATE,
    "ContractNo"        VARCHAR(10),
    "CDate"             DATE,
    "CExpiryDate"       DATE,
    "ContractFPath"     VARCHAR(200),   -- FTP path to contract document
    "FileFolder"        VARCHAR(200),   -- FTP path to file folder document

    -- ── HR meta ─────────────────────────────────────────────────────────
    "TicketType"        INTEGER,
    "AnualLeave"        INTEGER,
    "LastTicketDate"    DATE,
    "OffDay"            INTEGER,
    "SettlementDate"    DATE,
    "HRStatus"          INTEGER,

    -- ── Hired From ──────────────────────────────────────────────────────
    "HiredFrom"         VARCHAR(50),
    "HFContactName"     VARCHAR(50),
    "HFPhone"           VARCHAR(15),
    "HFDate"            DATE,
    "HFExpiryDate"      DATE,
    "HFDocument"        VARCHAR(200),   -- FTP path to hired-from document

    -- ── Hired By ────────────────────────────────────────────────────────
    "HiredBy"           VARCHAR(50),
    "HBContactName"     VARCHAR(50),
    "HBPhone"           VARCHAR(15),
    "HBDate"            DATE,
    "HBExpiryDate"      DATE,
    "HBDocument"        VARCHAR(200),   -- FTP path to hired-by document
    "NOCExpiry"         DATE,

    -- ── Visa ────────────────────────────────────────────────────────────
    "VisaNo"            VARCHAR(20),
    "VisaType"          INTEGER,
    "Entrydate"         DATE,
    "VIsaExpiry"        DATE,
    "Medicaldate"       DATE,
    "FingerDate"        DATE,
    "Deadline"          DATE,

    -- ── Shift ───────────────────────────────────────────────────────────
    "ShiftType"           INTEGER,

    -- ── Payroll ─────────────────────────────────────────────────────────
    "BasicPay"          NUMERIC(15,2),
    "OTRate"            NUMERIC(15,2),
    "HolidayOTRate"     NUMERIC(15,2),
    "Commission"        NUMERIC(15,2),
    "DefAllowance"      NUMERIC(15,2),
    "AccAllowance"      NUMERIC(15,2),
    "FoodAllowance"     NUMERIC(15,2),
    "TelAllowance"      NUMERIC(15,2),
    "TransAllowance"    NUMERIC(15,2),

    -- ── Vendor billing ──────────────────────────────────────────────────
    "FirmID"            INTEGER,
    "BillNHrs"          NUMERIC(15,2),
    "BillRate"          NUMERIC(15,2),
    "BillBasicPay"      NUMERIC(15,2),
    "BillOTRate"        NUMERIC(15,2),
    "BillHOTRate"       NUMERIC(15,2),

    -- ── Customer billing ────────────────────────────────────────────────
    "BillCustomer"      INTEGER,
    "CustomerHours"     NUMERIC(15,2),
    "CustomerRate"      NUMERIC(15,2),
    "CustomerBasicPay"  NUMERIC(15,2),
    "CustomerOTRate"    NUMERIC(15,2),
    "CustomerHoliRate"  NUMERIC(15,2),

    -- ── Mobile App / Attendance ──────────────────────────────────────────
    "MobApp"            INTEGER         DEFAULT 0,   -- 1=Yes, 0=No
    "AttendanceLoc"     INTEGER         DEFAULT 0,   -- 1=Fixed, 0=Flexible
    "AppPass"           VARCHAR(50),                 -- MD5 hash of app password
    "LocID"             INTEGER,                     -- FK → AttendanceLocations.LocID

    -- ── Misc ────────────────────────────────────────────────────────────
    "Remarks"           VARCHAR(300),
    "ImagePath"         VARCHAR(200),   -- FTP path to employee photo

    -- ── Primary key ─────────────────────────────────────────────────────
    CONSTRAINT "PK_Employees" PRIMARY KEY ("RegNo")
);
"""

CREATE_EMPLOYEES_INDEXES_SQL = [
    'CREATE INDEX IF NOT EXISTS "idx_employees_empname" ON "Employees" ("EmpName");',
    'CREATE INDEX IF NOT EXISTS "idx_employees_active"  ON "Employees" ("Active");',
    'CREATE INDEX IF NOT EXISTS "idx_employees_dept"    ON "Employees" ("Department");',
]

# ── Migration: drop orphaned columns from existing tables ─────────────────────
DROP_ORPHANED_COLUMNS_SQL = [
    'ALTER TABLE "Employees" DROP COLUMN IF EXISTS "AdmNo";',
    'ALTER TABLE "Employees" DROP COLUMN IF EXISTS "EmpStatus";',
    'ALTER TABLE "Employees" DROP COLUMN IF EXISTS "FSSTime";',
    'ALTER TABLE "Employees" DROP COLUMN IF EXISTS "FSETime";',
    'ALTER TABLE "Employees" DROP COLUMN IF EXISTS "SSSTime";',
    'ALTER TABLE "Employees" DROP COLUMN IF EXISTS "SSETime";',
]

# ── Migration: widen document path columns (VARCHAR 100 → 200) ───────────────
WIDEN_PATH_COLUMNS_SQL = [
    'ALTER TABLE "Employees" ALTER COLUMN "ContractFPath" TYPE VARCHAR(200);',
    'ALTER TABLE "Employees" ALTER COLUMN "FileFolder"    TYPE VARCHAR(200);',
    'ALTER TABLE "Employees" ALTER COLUMN "HFDocument"   TYPE VARCHAR(200);',
    'ALTER TABLE "Employees" ALTER COLUMN "HBDocument"   TYPE VARCHAR(200);',
]

ADD_NEW_COLUMNS_SQL = [
    'ALTER TABLE "Employees" ADD COLUMN IF NOT EXISTS "ReportTo"      INTEGER;',
    'ALTER TABLE "Employees" ADD COLUMN IF NOT EXISTS "ShiftType"     INTEGER;',
    # ── Mobile App / Attendance Location columns ──────────────────────────
    'ALTER TABLE "Employees" ADD COLUMN IF NOT EXISTS "MobApp"        INTEGER DEFAULT 0;',
    'ALTER TABLE "Employees" ADD COLUMN IF NOT EXISTS "AttendanceLoc" INTEGER DEFAULT 0;',
    'ALTER TABLE "Employees" ADD COLUMN IF NOT EXISTS "AppPass"       VARCHAR(50);',
    'ALTER TABLE "Employees" ADD COLUMN IF NOT EXISTS "LocID"         INTEGER;',
    'ALTER TABLE "Employees" ADD COLUMN IF NOT EXISTS "RejoinDate"    DATE;',

]


def ensure_employees_table(db_alias: str = 'customer_db') -> bool:
    """
    Create the Employees table + indexes if they don't exist,
    then apply any pending column migrations (idempotent).

    Returns True  → table was just created.
    Returns False → table already existed (migrations still applied).

    Safe to call on every request — the information_schema check is fast.
    Called automatically by BaseCRUD when table_creator=ensure_employees_table.
    """
    try:
        conn = connections[db_alias]

        # Fast existence check
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1 FROM information_schema.tables
                WHERE  table_schema = 'public'
                AND    table_name   = 'Employees'
            """)
            already_exists = cur.fetchone() is not None

        if not already_exists:
            # Brand-new table — create it (already has the correct columns)
            with conn.cursor() as cur:
                cur.execute(CREATE_EMPLOYEES_SQL)
                for idx_sql in CREATE_EMPLOYEES_INDEXES_SQL:
                    cur.execute(idx_sql)
            logger.info('[hrms] Created Employees table on db="%s"', db_alias)
            return True

        # Table exists — apply pending migrations idempotently
        with conn.cursor() as cur:
            # 1. Drop orphaned columns
            for sql in DROP_ORPHANED_COLUMNS_SQL:
                try:
                    cur.execute(sql)
                except Exception as e:
                    logger.debug('[hrms] Drop column skipped: %s', e)

            # 2. Widen document path columns to VARCHAR(200)
            for sql in WIDEN_PATH_COLUMNS_SQL:
                try:
                    cur.execute(sql)
                except Exception as e:
                    logger.debug('[hrms] Widen column skipped: %s', e)

            # 3. Add new columns (idempotent via IF NOT EXISTS)
            for sql in ADD_NEW_COLUMNS_SQL:
                try:
                    cur.execute(sql)
                except Exception as e:
                    logger.debug('[hrms] Add column skipped: %s', e)

        return False

    except (ProgrammingError, OperationalError) as e:
        logger.error('[hrms] ensure_employees_table failed: %s', e, exc_info=True)
        return False