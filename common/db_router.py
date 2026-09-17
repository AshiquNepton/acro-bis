# common/db_router.py

from common.middleware.database_middleware import get_customer_db


class CustomerDatabaseRouter:
    """
    Routes Django ORM queries to correct database.
    Raw SQL views (employee.py, form_design.py etc.) use
    connections[_db(request)] directly — the router only affects ORM.
    """

    # Django internals → default DB only
    DEFAULT_DB_APPS = frozenset({
        'sessions',
        'admin',
        'auth',
        'contenttypes',
        'messages',
    })

    # All business apps → customer DB
    CUSTOMER_DB_APPS = frozenset({
        'common',
        'inventory',
        'financial',
        'laundry',
        'restaurant',
        'reports',
        'core',
    })

    def db_for_read(self, model, **hints):
        app = model._meta.app_label
        if app in self.DEFAULT_DB_APPS:
            return 'default'
        # customer apps + any unknown app → customer DB
        return get_customer_db()

    def db_for_write(self, model, **hints):
        app = model._meta.app_label
        if app in self.DEFAULT_DB_APPS:
            return 'default'
        return get_customer_db()

    def allow_relation(self, obj1, obj2, **hints):
        a1 = obj1._meta.app_label
        a2 = obj2._meta.app_label
        # Same DB bucket → allow
        both_default  = a1 in self.DEFAULT_DB_APPS  and a2 in self.DEFAULT_DB_APPS
        both_customer = a1 not in self.DEFAULT_DB_APPS and a2 not in self.DEFAULT_DB_APPS
        if both_default or both_customer:
            return True
        return False

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.DEFAULT_DB_APPS:
            return db == 'default'
        if app_label in self.CUSTOMER_DB_APPS:
            return db == 'customer_db'
        return None
    


