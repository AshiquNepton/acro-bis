"""
common/models/customer.py

Defines the Customer domain — backed by the ChartOfAccounts + CustomerVendor
tables in each tenant's database.

This system uses raw SQL against a multi-tenant PostgreSQL database rather than
Django ORM migrations, so these are schema-definition helpers and typed
constants, not Django Model subclasses.

Tables
──────
  ChartOfAccounts  — master account record (shared with vendors, via MGroup)
  CustomerVendor   — extended party details (address, contacts, financials)

MGroup value for customers: 36
"""

# ── MGroup constant ─────────────────────────────────────────────────────────
CUSTOMER_MGROUP = 36

# ── DDL ─────────────────────────────────────────────────────────────────────

#: Core account table — shared with vendor records (distinguished by MGroup).
CHART_OF_ACCOUNTS_DDL = """
CREATE TABLE IF NOT EXISTS "ChartOfAccounts" (
    "AccountID"      INTEGER,
    "MGroup"         INTEGER,
    "GroupID"        INTEGER NOT NULL,
    "Description"    VARCHAR(100) NOT NULL,
    "Address1"       VARCHAR(50),
    "SDate"          TIMESTAMP,
    "Status"         VARCHAR(10),
    "AcCode"         VARCHAR(15),
    "Active"         SMALLINT,
    "AcUnder"        SMALLINT,
    "NREC"           SMALLINT,
    "AcName"         VARCHAR(100),
    "Approved"       INTEGER,
    "ApprovedBy"     INTEGER,
    "ApprovedDate"   TIMESTAMP,
    "ArabicDesc"     CHAR(100),
    "LockUGID"       CHAR(50),
    CONSTRAINT "PK_ChartOfAccounts" PRIMARY KEY ("GroupID", "Description"),
    CONSTRAINT "Duplicate_ACID" UNIQUE ("AccountID")
);
"""

#: Extended party details — one row per ChartOfAccounts record.
CUSTOMER_VENDOR_DDL = """
CREATE TABLE IF NOT EXISTS "CustomerVendor" (
    "AccountID"        INTEGER NOT NULL,
    "Address2"         VARCHAR(50),
    "Address3"         VARCHAR(50),
    "PinCode"          VARCHAR(10),
    "Phone"            VARCHAR(25),
    "PhoneRes"         VARCHAR(25),
    "Mobile"           VARCHAR(25),
    "Fax"              VARCHAR(25),
    "Email"            VARCHAR(50),
    "RUL"              VARCHAR(50),
    "Contact"          VARCHAR(30),
    "TINNO"            VARCHAR(15),
    "CST"              VARCHAR(15),
    "RepCode"          INTEGER,
    "PricingLevel"     SMALLINT,
    "LTDate"           TIMESTAMP,
    "LTAmount"         NUMERIC(19,4),
    "LPayDate"         TIMESTAMP,
    "LPayAmount"       NUMERIC(19,4),
    "CreditLimit"      NUMERIC(19,4),
    "CreditDys"        NUMERIC(19,4),
    "Discount"         NUMERIC(19,4),
    "Additions"        NUMERIC(19,4),
    "Oweight"          NUMERIC(19,4),
    "City"             INTEGER,
    "Area"             INTEGER,
    "District"         INTEGER,
    "State"            INTEGER,
    "AcType"           VARCHAR(10),
    "AltContact"       VARCHAR(30),
    "AltAddress1"      VARCHAR(30),
    "AltAddress2"      VARCHAR(30),
    "AltAddress3"      VARCHAR(30),
    "AltPinCode"       VARCHAR(10),
    "AltPhone"         VARCHAR(25),
    "AltMobile"        VARCHAR(25),
    "KGST"             VARCHAR(15),
    "DUEDATE"          TIMESTAMP,
    "InactDate"        TIMESTAMP,
    "Remarks"          VARCHAR(250),
    "ImagePath"        CHAR(50),
    "DiscPer"          NUMERIC(19,4),
    "RebatePer"        NUMERIC(19,4),
    "AdvtPer"          NUMERIC(19,4),
    "ManagementPer"    NUMERIC(19,4),
    "DisplayPer"       NUMERIC(19,4),
    "promotionPer"     NUMERIC(19,4),
    "ContName1"        CHAR(20),
    "ContDesig1"       INTEGER,
    "ContPH1"          CHAR(10),
    "ContFax1"         CHAR(10),
    "ContExt1"         CHAR(10),
    "ContMob1"         CHAR(10),
    "ContEmail1"       CHAR(20),
    "ContName2"        CHAR(20),
    "ContDesig2"       INTEGER,
    "ContPH2"          CHAR(10),
    "ContFax2"         CHAR(10),
    "ContExt2"         CHAR(10),
    "ContMob2"         CHAR(10),
    "ContEmail2"       CHAR(20),
    "ContName3"        CHAR(20),
    "ContDesig3"       INTEGER,
    "ContPH3"          CHAR(10),
    "ContFax3"         CHAR(10),
    "ContExt3"         CHAR(10),
    "ContMob3"         CHAR(10),
    "ContEmail3"       CHAR(20),
    "ContName4"        CHAR(20),
    "ContDesig4"       INTEGER,
    "ContPH4"          CHAR(10),
    "ContFax4"         CHAR(10),
    "ContExt4"         CHAR(10),
    "ContMob4"         CHAR(10),
    "ContEmail4"       CHAR(20),
    "ContName5"        CHAR(20),
    "ContDesig5"       INTEGER,
    "ContPH5"          CHAR(10),
    "ContFax5"         CHAR(10),
    "ContExt5"         CHAR(10),
    "ContMob5"         CHAR(10),
    "ContEmail5"       CHAR(20),
    "TransType"        INTEGER,
    "Inquiry"          INTEGER,
    "AName"            VARCHAR(50),
    "Aadd1"            VARCHAR(20),
    "Aadd2"            VARCHAR(20),
    "Aadd3"            VARCHAR(20),
    "Block"            INTEGER,
    "BlockReason"      VARCHAR(20),
    "WHID"             INTEGER,
    "VATNumber"        VARCHAR(20),
    "BuildingNo"       VARCHAR(20),
    "Street"           VARCHAR(100),
    "StreetNo"         VARCHAR(10),
    "DistrictVat"      VARCHAR(100),
    "CityVAT"          VARCHAR(100),
    "PostalCode"       VARCHAR(20),
    "CountryCode"      VARCHAR(10),
    "AdditionalNo"     VARCHAR(20),
    CONSTRAINT "PK_PartyDetails" PRIMARY KEY ("AccountID")
);
"""

#: Fields persisted in CustomerVendor on every save.
CUSTOMER_VENDOR_FIELDS = [
    'Address2', 'Address3', 'PinCode', 'City', 'Phone', 'Mobile',
    'Email', 'Fax', 'Contact', 'VATNumber', 'TINNO', 'CST',
    'CreditLimit', 'CreditDys', 'PricingLevel', 'Discount', 'Remarks',
    'ContName1', 'ContMob1', 'ContEmail1',
    'ContName2', 'ContMob2', 'ContEmail2',
    'AltAddress1', 'AltAddress2', 'AltPinCode',
    'AltContact', 'AltPhone', 'AltMobile',
]
