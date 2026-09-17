# # common/db_backend/base.py

# import threading
# from django.db.backends.postgresql.base import DatabaseWrapper as PostgresDatabaseWrapper

# _thread_locals = threading.local()


# def set_db_credentials(host, port, name, user, password):
#     _thread_locals.db_host     = host     or ''
#     _thread_locals.db_port     = str(port or '5432')
#     _thread_locals.db_name     = name     or ''
#     _thread_locals.db_user     = user     or ''
#     _thread_locals.db_password = password or ''


# def get_db_credentials():
#     return {
#         'host'    : getattr(_thread_locals, 'db_host',     ''),
#         'port'    : getattr(_thread_locals, 'db_port',     '5432'),
#         'name'    : getattr(_thread_locals, 'db_name',     ''),
#         'user'    : getattr(_thread_locals, 'db_user',     ''),
#         'password': getattr(_thread_locals, 'db_password', ''),
#     }


# class DatabaseWrapper(PostgresDatabaseWrapper):
#     """
#     Custom PostgreSQL backend that bypasses settings.DATABASES['NAME']
#     validation and reads credentials from thread-locals at connection time.
#     """

#     def get_connection_params(self):
#         creds = get_db_credentials()

#         # Build params directly — do NOT call super() because it validates
#         # settings.DATABASES[alias]['NAME'] which we intentionally leave empty.
#         settings_dict = self.settings_dict
#         conn_params = {
#             'host'            : creds['host'],
#             'port'            : int(creds['port'] or 5432),
#             'dbname'          : creds['name'],
#             'user'            : creds['user'],
#             'password'        : creds['password'],
#             'connect_timeout' : settings_dict.get('OPTIONS', {}).get('connect_timeout', 10),
#         }

#         # Merge any extra OPTIONS (excluding connect_timeout already set)
#         options = settings_dict.get('OPTIONS', {}).copy()
#         options.pop('connect_timeout', None)
#         options.pop('service', None)
#         conn_params.update(options)

#         return conn_params















# common/db_backend/base.py

import os
import logging
import threading
from django.db.backends.postgresql.base import DatabaseWrapper as PostgresDatabaseWrapper

logger = logging.getLogger(__name__)

_thread_locals = threading.local()


def set_db_credentials(host, port, name, user, password):
    _thread_locals.db_host     = host     or ''
    _thread_locals.db_port     = str(port or '5432')
    _thread_locals.db_name     = name     or ''
    _thread_locals.db_user     = user     or ''
    _thread_locals.db_password = password or ''


def get_db_credentials():
    host = getattr(_thread_locals, 'db_host', '')
    if host in ('localhost', '127.0.0.1', '') and os.getenv('DB_HOST'):
        host = os.getenv('DB_HOST')
        
    return {
        'host'    : host,
        'port'    : getattr(_thread_locals, 'db_port',     '5432'),
        'name'    : getattr(_thread_locals, 'db_name',     ''),
        'user'    : getattr(_thread_locals, 'db_user',     ''),
        'password': getattr(_thread_locals, 'db_password', ''),
    }


class DatabaseWrapper(PostgresDatabaseWrapper):
    """
    Custom PostgreSQL backend that bypasses settings.DATABASES['NAME']
    validation and reads credentials from thread-locals at connection time.
    """

    def get_connection_params(self):
        creds = get_db_credentials()

        settings_dict = self.settings_dict
        conn_params = {
            'host'            : creds['host'],
            'port'            : int(creds['port'] or 5432),
            'dbname'          : creds['name'],
            'user'            : creds['user'],
            'password'        : creds['password'],
            'connect_timeout' : settings_dict.get('OPTIONS', {}).get('connect_timeout', 10),
        }

        options = settings_dict.get('OPTIONS', {}).copy()
        options.pop('connect_timeout', None)
        options.pop('service', None)
        conn_params.update(options)

        return conn_params

    def get_new_connection(self, conn_params):
        """
        Open the connection using the tenant host stored in the softwares
        table (conn_params['host']). If that host is unreachable (e.g. a
        production-only DNS name that doesn't resolve from a dev machine),
        retry once using DB_HOST from .env — same dbname/user/password,
        host only. The DB-stored host is always tried first; there is no
        caching of the fallback across requests.
        """
        try:
            return super().get_new_connection(conn_params)
        except Exception as exc:
            fallback_host = os.getenv('DB_HOST', '').strip()
            primary_host  = conn_params.get('host') or ''

            if not fallback_host or fallback_host == primary_host:
                raise

            logger.warning(
                "customer_db: could not connect to host '%s' (%s) — "
                "retrying with DB_HOST fallback '%s'",
                primary_host, exc, fallback_host
            )

            fallback_params = dict(conn_params)
            fallback_params['host'] = fallback_host
            return super().get_new_connection(fallback_params)