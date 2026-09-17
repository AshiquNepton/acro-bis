# common/services/inventory_service.py
"""
Universal Inventory Service
===========================
Shared service that ANY module (Laundry, Restaurant, Logistics, Gym, POS)
can import and call directly without writing custom inventory queries.

Key Operations:
1. get_stock(item_code, warehouse_code=None)
2. record_movement(item_code, movement_type, quantity, unit_cost, reference_no, warehouse_code, remarks)
3. check_availability(item_code, required_qty, warehouse_code=None)
4. get_item_details(item_code)

Automatically posts or triggers accounting / financial transactions if requested.
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any

from django.db import connections, transaction
from common.middleware.database_middleware import get_customer_db
from errors.exceptions import InsufficientStockError, RecordNotFoundError

logger = logging.getLogger(__name__)


class UniversalInventoryService:
    """Reusable inventory engine for all business verticals."""

    @staticmethod
    def _ensure_tables(db_alias: str):
        """Ensures core stock movement and item tables exist in tenant database."""
        with connections[db_alias].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS "StockMovement" (
                    "MovementId" SERIAL PRIMARY KEY,
                    "ItemCode" VARCHAR(50) NOT NULL,
                    "MovementType" VARCHAR(10) NOT NULL, -- 'IN', 'OUT', 'ADJ', 'TRANSFER'
                    "Quantity" NUMERIC(14, 4) NOT NULL,
                    "UnitCost" NUMERIC(14, 4) DEFAULT 0,
                    "WarehouseCode" VARCHAR(50),
                    "ReferenceNo" VARCHAR(100),
                    "Remarks" VARCHAR(255),
                    "MovementDate" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    "SourceModule" VARCHAR(30) -- 'laundry', 'restaurant', 'gym', 'logistics', etc.
                );
                CREATE INDEX IF NOT EXISTS idx_stock_item_wh ON "StockMovement" ("ItemCode", "WarehouseCode");
            """)

    @classmethod
    def get_stock(cls, item_code: str, warehouse_code: Optional[str] = None, db_alias: Optional[str] = None) -> Decimal:
        """
        Returns current on-hand stock for an item (optionally filtered by warehouse).
        Calculates: SUM(IN) - SUM(OUT) +/- SUM(ADJ).
        """
        db = db_alias or get_customer_db()
        cls._ensure_tables(db)

        query = """
            SELECT COALESCE(SUM(
                CASE 
                    WHEN "MovementType" = 'IN' THEN "Quantity"
                    WHEN "MovementType" = 'OUT' THEN -"Quantity"
                    WHEN "MovementType" = 'ADJ' THEN "Quantity"
                    ELSE 0
                END
            ), 0)
            FROM "StockMovement"
            WHERE "ItemCode" = %s
        """
        params = [item_code]
        if warehouse_code:
            query += ' AND "WarehouseCode" = %s'
            params.append(warehouse_code)

        with connections[db].cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return Decimal(str(row[0])) if row else Decimal('0')

    @classmethod
    def check_availability(cls, item_code: str, required_qty: Decimal, warehouse_code: Optional[str] = None, db_alias: Optional[str] = None) -> bool:
        """Returns True if sufficient stock is available."""
        current_stock = cls.get_stock(item_code, warehouse_code, db_alias)
        return current_stock >= Decimal(str(required_qty))

    @classmethod
    def record_movement(
        cls,
        item_code: str,
        movement_type: str,
        quantity: Decimal,
        reference_no: str,
        source_module: str,
        unit_cost: Decimal = Decimal('0'),
        warehouse_code: Optional[str] = 'main',
        remarks: Optional[str] = '',
        allow_negative: bool = False,
        db_alias: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Records an inventory stock movement from any vertical.
        
        Example calls:
            # From Laundry (detergent consumption):
            UniversalInventoryService.record_movement('DET-01', 'OUT', 2.5, 'ORD-1002', 'laundry')

            # From Restaurant / POS (ingredient or item sale):
            UniversalInventoryService.record_movement('COKE-CAN', 'OUT', 1, 'BILL-5401', 'restaurant')

            # From Gym (supplement sale):
            UniversalInventoryService.record_movement('PROT-SHAKE', 'OUT', 1, 'POS-902', 'gym')
        """
        db = db_alias or get_customer_db()
        cls._ensure_tables(db)

        movement_type = movement_type.upper().strip()
        qty = Decimal(str(quantity))

        # Check stock for OUT movements if negative stock is disallowed
        if movement_type == 'OUT' and not allow_negative:
            current_stock = cls.get_stock(item_code, warehouse_code, db)
            if current_stock < qty:
                raise InsufficientStockError(
                    f"Insufficient stock for '{item_code}'. Available: {current_stock}, Requested: {qty}"
                )

        with connections[db].cursor() as cursor:
            cursor.execute("""
                INSERT INTO "StockMovement" 
                ("ItemCode", "MovementType", "Quantity", "UnitCost", "WarehouseCode", "ReferenceNo", "Remarks", "SourceModule")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING "MovementId"
            """, [
                item_code, movement_type, qty, unit_cost,
                warehouse_code, reference_no, remarks, source_module
            ])
            movement_id = cursor.fetchone()[0]

        logger.info(
            "Stock movement recorded [%s] item=%s type=%s qty=%s ref=%s module=%s",
            movement_id, item_code, movement_type, qty, reference_no, source_module
        )

        return {
            'success': True,
            'movement_id': movement_id,
            'item_code': item_code,
            'remaining_stock': cls.get_stock(item_code, warehouse_code, db),
        }
