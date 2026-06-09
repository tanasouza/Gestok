"""
Django settings for gestok_project project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def load_local_env():
    env_file = BASE_DIR / '.env'
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('GESTOK_SECRET_KEY', 'django-insecure-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('GESTOK_DEBUG', 'True').lower() in {'1', 'true', 'yes', 'on'}

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('GESTOK_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
    if host.strip()
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'drf_spectacular',
    'widget_tweaks',

    # Local apps
    'core',
    'accounts',
    'products',
    'sales',
    'cashier',
    'reports',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.ThreadLocalMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.FirstAccessMiddleware',
]

ROOT_URLCONF = 'gestok_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.gestok_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestok_project.wsgi.application'


# Database — MySQL / MariaDB
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('GESTOK_DB_NAME', 'gestok_db'),
        'USER': os.getenv('GESTOK_DB_USER', 'root'),
        'PASSWORD': os.getenv('GESTOK_DB_PASSWORD', ''),
        'HOST': os.getenv('GESTOK_DB_HOST', 'localhost'),
        'PORT': os.getenv('GESTOK_DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.MatriculaBackend',
    'django.contrib.auth.backends.ModelBackend',
]


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        },
    },
]


# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Manaus'
USE_I18N = True
USE_TZ = True
USE_L10N = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'


# Authentication
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'


# Django Messages — map tags for Bootstrap
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'info',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}


# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}


# DRF Spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'Gestok API',
    'DESCRIPTION': 'API do sistema Gestok - Portal de Gestão de Inventário e Vendas',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
