# core/management/commands/migrate_logos.py
"""
Management command: migrate_logos
==================================
Adds the four logo path columns to the Organization table in customer_db.

Safe to run multiple times (uses ADD COLUMN IF NOT EXISTS).

Usage:
    python manage.py migrate_logos
"""

from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    help = 'Add HeaderFullLogo, HeaderSideLogo, FooterFullLogo, FooterSideLogo to Organization'

    def handle(self, *args, **options):
        db_alias = 'customer_db'

        sql = """
            ALTER TABLE "Organization"
                ADD COLUMN IF NOT EXISTS "HeaderFullLogo"  VARCHAR(500),
                ADD COLUMN IF NOT EXISTS "HeaderSideLogo"  VARCHAR(500),
                ADD COLUMN IF NOT EXISTS "FooterFullLogo"  VARCHAR(500),
                ADD COLUMN IF NOT EXISTS "FooterSideLogo"  VARCHAR(500);
        """

        try:
            with connections[db_alias].cursor() as cur:
                cur.execute(sql)
            self.stdout.write(
                self.style.SUCCESS(
                    '✔  Logo columns added (or already existed) on '
                    f'"{db_alias}" → Organization'
                )
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'✗  Migration failed on "{db_alias}": {e}')
            )
            raise