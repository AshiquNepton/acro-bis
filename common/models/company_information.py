# common/models/company_information.py

from django.db import models




class Organization(models.Model):
    """
    Mirrors the Organization table in the customer PostgreSQL database.
    All field names match the DB column names exactly (PascalCase).
    """

    CompanyId    = models.IntegerField(primary_key=True, db_column='CompanyId')
    CompanyName  = models.CharField(max_length=300,  db_column='CompanyName')
    ArabicName   = models.CharField(max_length=300,  db_column='ArabicName',   null=True, blank=True)
    Subtitle     = models.CharField(max_length=300,  db_column='Subtitle',     null=True, blank=True)
    Address1     = models.CharField(max_length=300,  db_column='Address1',     null=True, blank=True)
    Address2     = models.CharField(max_length=300,  db_column='Address2',     null=True, blank=True)
    Address3     = models.CharField(max_length=300,  db_column='Address3',     null=True, blank=True)
    Phone        = models.CharField(max_length=300,  db_column='Phone',        null=True, blank=True)
    Mobile       = models.CharField(max_length=300,  db_column='Mobile',       null=True, blank=True)
    Url          = models.CharField(max_length=300,  db_column='Url',          null=True, blank=True)
    Email        = models.CharField(max_length=254,  db_column='Email',        null=True, blank=True)
    TinNo        = models.CharField(max_length=300,  db_column='TinNo',        null=True, blank=True)
    CrNo         = models.CharField(max_length=300,  db_column='CrNo',         null=True, blank=True)
    LicenseNo    = models.CharField(max_length=300,  db_column='LicenseNo',    null=True, blank=True)
    BuildingNo   = models.CharField(max_length=300,  db_column='BuildingNo',   null=True, blank=True)
    StreetName   = models.CharField(max_length=300,  db_column='StreetName',   null=True, blank=True)
    Zone         = models.CharField(max_length=300,  db_column='Zone',         null=True, blank=True)
    Area         = models.CharField(max_length=300,  db_column='Area',         null=True, blank=True)
    City         = models.CharField(max_length=300,  db_column='City',         null=True, blank=True)
    State        = models.CharField(max_length=300,  db_column='State',        null=True, blank=True)
    District     = models.CharField(max_length=300,  db_column='District',     null=True, blank=True)
    PoBox        = models.CharField(max_length=300,  db_column='PoBox',        null=True, blank=True)
    PlotIdentification = models.CharField(max_length=300, db_column='PlotIdentification', null=True, blank=True)
    AccountNumber = models.CharField(max_length=300, db_column='AccountNumber', null=True, blank=True)
    AccountName  = models.CharField(max_length=300,  db_column='AccountName',  null=True, blank=True)
    Branch       = models.CharField(max_length=300,  db_column='Branch',       null=True, blank=True)
    Ifsc         = models.CharField(max_length=300,  db_column='Ifsc',         null=True, blank=True)
    PayerId      = models.CharField(max_length=300,  db_column='PayerId',      null=True, blank=True)
    PayerBank    = models.CharField(max_length=300,  db_column='PayerBank',    null=True, blank=True)
    PayerIban    = models.CharField(max_length=300,  db_column='PayerIban',    null=True, blank=True)
    PeriodFrom   = models.DateField(db_column='PeriodFrom')
    PeriodTo     = models.DateField(db_column='PeriodTo')
    DefaultDb    = models.SmallIntegerField(db_column='DefaultDb', null=True, blank=True, default=0)
    BusinessType = models.SmallIntegerField(db_column='BusinessType')
    CreatedAt    = models.DateTimeField(db_column='CreatedAt',    null=True, blank=True, auto_now_add=False)
    

    # ── New column ────────────────────────────────────────────────────────────
    DbName       = models.CharField(max_length=300,  db_column='DbName',       null=True, blank=True)
    HeaderFullLogo = models.CharField(max_length=500, null=True, blank=True)
    HeaderSideLogo = models.CharField(max_length=500, null=True, blank=True)
    FooterFullLogo = models.CharField(max_length=500, null=True, blank=True)
    FooterSideLogo = models.CharField(max_length=500, null=True, blank=True)
    

    class Meta:
        db_table = 'Organization'
        managed  = False          # Table is managed outside Django migrations


def ensure_organization_logo_columns(db_alias: str = 'customer_db') -> None:
    """
    Adds logo columns to Organization table if they don't exist.
    Safe to call multiple times — uses ADD COLUMN IF NOT EXISTS.
    """
    from django.db import connections
    import logging
    logger = logging.getLogger(__name__)

    _LOGO_COLS = [
        ('HeaderFullLogo', 'VARCHAR(500)'),
        ('HeaderSideLogo', 'VARCHAR(500)'),
        ('FooterFullLogo', 'VARCHAR(500)'),
        ('FooterSideLogo', 'VARCHAR(500)'),
    ]

    try:
        conn = connections[db_alias]
        with conn.cursor() as cur:
            for col_name, col_type in _LOGO_COLS:
                cur.execute(
                    f'ALTER TABLE "Organization" '
                    f'ADD COLUMN IF NOT EXISTS "{col_name}" {col_type}'
                )
        logger.info('[ensure_organization_logo_columns] done on db=%s', db_alias)
    except Exception as e:
        logger.warning('[ensure_organization_logo_columns] %s', e)

