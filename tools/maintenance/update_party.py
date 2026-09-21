import os

path = 'common/views/party_master.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

ensure_tables = '''def ensure_party_tables(db_alias):
    try:
        with connections[db_alias].cursor() as cur:
            cur.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'ChartOfAccounts'")
            if not cur.fetchone():
                cur.execute("""
                    CREATE TABLE "ChartOfAccounts" (
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
                """)
                logger.info('Created ChartOfAccounts table.')

            cur.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'CustomerVendor'")
            if not cur.fetchone():
                cur.execute("""
                    CREATE TABLE "CustomerVendor" (
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
                        "RepCode\"          INTEGER,
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
                """)
                logger.info('Created CustomerVendor table.')
    except Exception as e:
        logger.error(f"Error ensuring tables: {e}")
'''

if 'def ensure_party_tables' not in code:
    code = code.replace('def save_party(request, mgroup):', ensure_tables + '\n\ndef save_party(request, mgroup):')
    code = code.replace('db_alias = _get_db(request)', 'db_alias = _get_db(request)\n        ensure_party_tables(db_alias)')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(code)
    print("Tables logic added")
else:
    print("Already added")
