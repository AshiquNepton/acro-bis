# common/middleware/database_middleware.py

from django.db import connections
from django.db.utils import OperationalError, ProgrammingError
import threading

_thread_locals = threading.local()


def get_customer_db():
    return getattr(_thread_locals, 'customer_db', 'customer_db')


def set_customer_db(db_alias):
    _thread_locals.customer_db = db_alias


class DynamicDatabaseMiddleware:
    """
    Sets customer DB credentials in thread-locals every request.
    common/db_backend/base.py reads them when opening connections.

    Required MIDDLEWARE order in settings.py:
        'django.contrib.sessions.middleware.SessionMiddleware',
        'common.middleware.database_middleware.DynamicDatabaseMiddleware',
        ...
    """

    NO_SESSION_PATHS = ('/static/', '/media/', '/favicon.ico', '/admin/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from common.db_backend.base import set_db_credentials

        if any(request.path.startswith(p) for p in self.NO_SESSION_PATHS):
            set_customer_db('customer_db')
            request._customer_db_configured = True
            return self.get_response(request)

        try:
            db_host     = request.session.get('db_host')
            db_name     = request.session.get('db_name')
            db_user     = request.session.get('db_user')
            db_password = request.session.get('db_password')
            db_port     = request.session.get('db_port', '5432')

            if all([db_host, db_name, db_user, db_password]):
                current_creds = (str(db_host), str(db_port), str(db_name), str(db_user), str(db_password))
                prev_creds = getattr(_thread_locals, 'active_conn_creds', None)

                set_db_credentials(db_host, db_port, db_name, db_user, db_password)

                # Only close and reset connection if tenant credentials changed
                if current_creds != prev_creds:
                    try:
                        connections['customer_db'].close()
                    except Exception:
                        pass
                    _thread_locals.active_conn_creds = current_creds
                    print(f"[MIDDLEWARE] customer_db -> {db_host}/{db_name} (connected)")
            else:
                set_db_credentials('', '5432', '', '', '')
                if getattr(_thread_locals, 'active_conn_creds', None) is not None:
                    try:
                        connections['customer_db'].close()
                    except Exception:
                        pass
                    _thread_locals.active_conn_creds = None
                print("[MIDDLEWARE] No session credentials")

        except (ProgrammingError, OperationalError) as e:
            print(f"[MIDDLEWARE] DB error: {e}")
            set_db_credentials('', '5432', '', '', '')
        except Exception as e:
            print(f"[MIDDLEWARE] Error: {e}")
            set_db_credentials('', '5432', '', '', '')

        set_customer_db('customer_db')
        request._customer_db_configured = True
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, (OperationalError, ProgrammingError)):
            try:
                connections['customer_db'].close()
            except Exception:
                pass
        return None