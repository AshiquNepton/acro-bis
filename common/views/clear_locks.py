from django.http import JsonResponse
from common.middleware.database_middleware import get_customer_db
from django.db import connections

from core.crud import fetch_tuples

def clear_locks(request):
    db_alias = get_customer_db()
    # Terminate all connections to the current DB except this one
    terminated = fetch_tuples(db_alias, """
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = current_database()
          AND pid <> pg_backend_pid()
          AND state IN ('idle in transaction', 'active');
    """)
    return JsonResponse({"terminated": len(terminated), "details": terminated})
