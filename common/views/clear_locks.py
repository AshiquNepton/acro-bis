from django.http import JsonResponse
from common.middleware.database_middleware import get_customer_db
from django.db import connections

def clear_locks(request):
    db_alias = get_customer_db()
    with connections[db_alias].cursor() as cur:
        # Terminate all connections to the current DB except this one
        cur.execute("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = current_database()
              AND pid <> pg_backend_pid()
              AND state IN ('idle in transaction', 'active');
        """)
        terminated = cur.fetchall()
    return JsonResponse({"terminated": len(terminated), "details": terminated})
