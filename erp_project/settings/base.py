# erp_project/settings/base.py
import os
from pathlib import Path
import sys

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Security settings
SECRET_KEY = 'django-insecure-your-secret-key-change-this-in-production'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Project apps
    'core',
    'common',
    'inventory',
    'financial',
    'reports',
    'laundry',
    'restaurant',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',                    # 1 — populates request.session
    'common.middleware.database_middleware.DynamicDatabaseMiddleware',          # 2 — reads session for DB creds
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'common.middleware.auth.AuthenticationMiddleware',                          # last
]

ROOT_URLCONF = 'erp_project.urls'
LOGIN_URL = ''

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'common' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'common.views.context_processors.company_context',
                'common.views.context_processors.global_settings_config',
                'common.views.context_processors.sidebar_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'erp_project.wsgi.application'

# ============================================================================
# OPTIMIZED DATABASE CONFIGURATION
# ============================================================================

try:
    from dotenv import load_dotenv
    
    # Load environment variables
    env_path = BASE_DIR / '.env'
    load_dotenv(env_path)
    
    # Get MAIN database credentials (for Django sessions only)
    db_host = os.getenv('DB_HOST', '')
    db_port = os.getenv('PORT', '5432')
    db_name = os.getenv('DB_NAME', '')
    db_user = os.getenv('DB_USER', '')
    db_password = os.getenv('DB_PASSWORD', '')
    
    # Configure MAIN database (ONLY for Django sessions, auth, admin)
    if db_host and db_name and db_user:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': db_name,
                'USER': db_user,
                'PASSWORD': db_password,
                'HOST': db_host,
                'PORT': db_port,
                'CONN_MAX_AGE': 600,  # Connection pooling - 10 minutes
                'OPTIONS': {
                    'connect_timeout': 10,
                    'options': '-c statement_timeout=10000',  # 10 second query timeout
                },
            }
        }
        print(f"[OK] MAIN DB configured: {db_host}/{db_name}")
    else:
        # SQLite fallback
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'main.db',
            }
        }
        print("[WARN] Using SQLite for MAIN DB")
        
except Exception as e:
    # SQLite fallback on error
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'main.db',
        }
    }
    print(f"[WARN] Database config error: {e}")

# CUSTOMER DATABASE - Configured dynamically by middleware
# This placeholder is replaced at runtime with actual customer credentials
DATABASES['customer_db'] = {
    # Custom backend — reads credentials from thread-locals at connection time.
    # This guarantees the correct PostgreSQL server is used regardless of
    # Django's connection wrapper caching.
    'ENGINE'            : 'common.db_backend',
    # These are fallback values only — middleware overwrites via set_db_credentials()
    'NAME'              : '',
    'USER'              : '',
    'PASSWORD'          : '',
    'HOST'              : 'localhost',
    'PORT'              : '5432',
    'CONN_MAX_AGE'      : 0,
    'CONN_HEALTH_CHECKS': False,
    'ATOMIC_REQUESTS'   : False,
    'AUTOCOMMIT'        : True,
    'OPTIONS'           : {'connect_timeout': 10},
    'TIME_ZONE'         : 'Asia/Qatar',
    'TEST'              : {
        'CHARSET': None, 'COLLATION': None, 'NAME': None, 'MIRROR': None,
    },
}

# ============================================================================
# DATABASE ROUTER - Routes queries to correct database
# ============================================================================
DATABASE_ROUTERS = ['common.db_router.CustomerDatabaseRouter']

# ============================================================================
# QUERY OPTIMIZATION SETTINGS
# ============================================================================

# Disable persistent connections in development (easier debugging)
# In production, keep CONN_MAX_AGE = 600 for connection pooling
if DEBUG:
    # Development: Fresh connections (easier to debug)
    # DATABASES['default']['CONN_MAX_AGE'] = 0
    # DATABASES['customer_db']['CONN_MAX_AGE'] = 0
    pass  # Keep pooling even in dev for better performance

# ============================================================================
# SESSION CONFIGURATION
# ============================================================================


FTP_HOST     = os.environ.get('FTP_HOST', '')
FTP_PORT     = int(os.environ.get('FTP_PORT', 21))
FTP_USER     = os.environ.get('FTP_USER', '')
FTP_PASSWORD = os.environ.get('FTP_PASSWORD', '')
FTP_ROOT     = os.environ.get('FTP_ROOT', '/erp')


# Use database sessions (stored in default DB)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = False  # Only save when modified
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# ============================================================================
# PASSWORD VALIDATION
# ============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================================================
# INTERNATIONALIZATION
# ============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Qatar'
USE_I18N = True
USE_TZ = True

# ============================================================================
# STATIC FILES
# ============================================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR / 'common' / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',  # Change to DEBUG to see all SQL queries
            'propagate': False,
        },
        'common': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory
(BASE_DIR / 'logs').mkdir(exist_ok=True)