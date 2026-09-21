import logging
import re
from django.db import connections
from common.middleware.database_middleware import get_customer_db

logger = logging.getLogger(__name__)

def generate_next_code(
    table: str, 
    code_column: str, 
    order_column: str, 
    prefix: str, 
    db_alias: str = None, 
    where_clause: str = None, 
    where_params: list = None
) -> str:
    """
    Generic utility to generate the next consecutive string code from a database table.
    Used across verticals (e.g. CUST-0001, ITM-0001, VEND-0001).

    Args:
        table (str): The name of the database table.
        code_column (str): The column containing the string code (e.g. 'AcCode', 'ItemCode').
        order_column (str): The column to order by descending (e.g. 'AccountID', 'ItemID').
        prefix (str): The default prefix to use if no records exist (e.g. 'CUST').
        db_alias (str, optional): The database connection alias. Defaults to customer_db.
        where_clause (str, optional): Additional SQL for filtering (e.g. '"MGroup" = %s').
        where_params (list, optional): Parameters for the where_clause.

    Returns:
        str: The next generated code string (e.g. 'CUST-0043').
    """
    try:
        db = db_alias or get_customer_db()
        sql = f'SELECT "{code_column}" FROM "{table}"'
        params = where_params or []
        
        if where_clause:
            sql += f' WHERE {where_clause}'
            
        sql += f' ORDER BY "{order_column}" DESC LIMIT 1'
        
        with connections[db].cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            
            if not row or not row[0]:
                return f'{prefix}-0001'
                
            code_str = str(row[0])
            match = re.search(r'(\d+)$', code_str)
            
            if match:
                extracted_prefix = code_str[:match.start()]
                num_str = match.group(1)
                # Increment the number but preserve the exact padding width
                return f"{extracted_prefix}{int(num_str) + 1:0{len(num_str)}d}"
                
            # If no number found at the end, append -0001
            return f"{code_str}-0001"
            
    except Exception as e:
        logger.error('[generate_next_code] Failed for %s: %s', table, e)
        return f'{prefix}-0001'
