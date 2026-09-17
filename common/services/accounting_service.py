# common/services/accounting_service.py
"""
Universal Accounting & General Ledger Service
=============================================
Shared double-entry accounting engine for ALL business verticals.

Any module (Inventory, Laundry, Restaurant POS, Logistics, Gym)
posts financial entries by calling this service.

Key Operations:
1. post_journal_entry(voucher_type, reference_no, narration, entries, source_module)
2. get_account_balance(account_code)
3. ensure_accounting_tables()
"""

import logging
from decimal import Decimal
from typing import List, Dict, Any, Optional

from django.db import connections, transaction
from common.middleware.database_middleware import get_customer_db
from errors.exceptions import ValidationError

logger = logging.getLogger(__name__)


class UniversalAccountingService:
    """Universal Double-Entry Accounting Service for all ERP verticals."""

    @staticmethod
    def _ensure_tables(db_alias: str):
        """Ensures core ledger tables exist in tenant customer database."""
        with connections[db_alias].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS "GLVoucher" (
                    "VoucherId" SERIAL PRIMARY KEY,
                    "VoucherType" VARCHAR(20) NOT NULL, -- 'SALES', 'PURCHASE', 'RECEIPT', 'PAYMENT', 'JOURNAL'
                    "VoucherDate" DATE DEFAULT CURRENT_DATE,
                    "ReferenceNo" VARCHAR(100),
                    "Narration" VARCHAR(300),
                    "SourceModule" VARCHAR(30), -- 'laundry', 'restaurant', 'inventory', 'gym', etc.
                    "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS "GLVoucherLine" (
                    "LineId" SERIAL PRIMARY KEY,
                    "VoucherId" INTEGER REFERENCES "GLVoucher"("VoucherId") ON DELETE CASCADE,
                    "AccountCode" VARCHAR(50) NOT NULL,
                    "Debit" NUMERIC(14, 2) DEFAULT 0,
                    "Credit" NUMERIC(14, 2) DEFAULT 0,
                    "LineNarration" VARCHAR(255)
                );

                CREATE INDEX IF NOT EXISTS idx_gl_acc ON "GLVoucherLine" ("AccountCode");
            """)

    @classmethod
    def post_journal_entry(
        cls,
        voucher_type: str,
        reference_no: str,
        narration: str,
        entries: List[Dict[str, Any]],
        source_module: str,
        voucher_date: Optional[str] = None,
        db_alias: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Posts a balanced double-entry voucher.
        
        Args:
            voucher_type: e.g. 'SALES', 'PURCHASE', 'PAYMENT'
            reference_no: Invoice / Bill / Order reference
            narration: Explanation
            entries: List of dicts, each having:
                     {'account_code': '...', 'debit': Decimal, 'credit': Decimal, 'narration': '...'}
            source_module: 'inventory', 'laundry', 'restaurant', 'gym', 'logistics'
        
        Enforces: Total Debits == Total Credits (Zero Imbalance).
        """
        db = db_alias or get_customer_db()
        cls._ensure_tables(db)

        total_debit = Decimal('0')
        total_credit = Decimal('0')

        for e in entries:
            deb = Decimal(str(e.get('debit', 0)))
            crd = Decimal(str(e.get('credit', 0)))
            total_debit += deb
            total_credit += crd

        # Validate balance
        if abs(total_debit - total_credit) > Decimal('0.001'):
            raise ValidationError(
                f"Voucher out of balance! Total Debit: {total_debit}, Total Credit: {total_credit}"
            )

        with connections[db].cursor() as cursor:
            # 1. Insert Voucher Header
            cursor.execute("""
                INSERT INTO "GLVoucher" 
                ("VoucherType", "ReferenceNo", "Narration", "SourceModule", "VoucherDate")
                VALUES (%s, %s, %s, %s, COALESCE(%s::date, CURRENT_DATE))
                RETURNING "VoucherId"
            """, [voucher_type, reference_no, narration, source_module, voucher_date])
            voucher_id = cursor.fetchone()[0]

            # 2. Insert Lines
            for e in entries:
                cursor.execute("""
                    INSERT INTO "GLVoucherLine" 
                    ("VoucherId", "AccountCode", "Debit", "Credit", "LineNarration")
                    VALUES (%s, %s, %s, %s, %s)
                """, [
                    voucher_id,
                    e['account_code'],
                    Decimal(str(e.get('debit', 0))),
                    Decimal(str(e.get('credit', 0))),
                    e.get('narration', narration),
                ])

        logger.info(
            "GL Voucher posted [%s] type=%s total=%s source=%s ref=%s",
            voucher_id, voucher_type, total_debit, source_module, reference_no
        )

        return {
            'success': True,
            'voucher_id': voucher_id,
            'total_amount': total_debit,
        }

    @classmethod
    def get_account_balance(cls, account_code: str, db_alias: Optional[str] = None) -> Decimal:
        """Calculates current net balance: SUM(Debit) - SUM(Credit)."""
        db = db_alias or get_customer_db()
        cls._ensure_tables(db)

        with connections[db].cursor() as cursor:
            cursor.execute("""
                SELECT COALESCE(SUM("Debit" - "Credit"), 0)
                FROM "GLVoucherLine"
                WHERE "AccountCode" = %s
            """, [account_code])
            row = cursor.fetchone()
            return Decimal(str(row[0])) if row else Decimal('0')
