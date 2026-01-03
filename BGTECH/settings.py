import os
from pathlib import Path
import dj_database_url
from celery.schedules import crontab
from dotenv import load_dotenv  # <-- Add this


# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


# --- SECURITY SETTINGS ---
# Pull the secret key from an environment variable
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

DEBUG = False
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'bgtech.com']  # Adjust this to your domain in production (e.g., ['bgtech.com'])
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']

# --- APPLICATION DEFINITION ---
INSTALLED_APPS = [
    'django_summernote',
    'users.apps.UsersConfig',
    'portech.apps.PortechConfig',
    'widget_tweaks',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic', # For serving static files in production
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Place right after SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'BGTECH.urls'
WSGI_APPLICATION = 'BGTECH.wsgi.application'

# --- TEMPLATES ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'users.context_processors.app_settings_processor',
            ],
        },
    },
]

# --- DATABASE CONFIGURATION ---
# Uses SQLite locally, but switches to DATABASE_URL (PostgreSQL/MySQL) if available on host
DATABASES = {
    'default': dj_database_url.config(
        # default=os.environ.get('DATABASE_URL'),
        default = BASE_DIR / 'db.sqlite3',
        conn_max_age=600
    )
}

# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True

# --- AUTHENTICATION ---
AUTH_USER_MODEL = 'users.CustomUser'
LOGIN_URL = '/bg-admin/login/'
LOGOUT_REDIRECT_URL = '/bg-admin/login/'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- DEPLOYMENT SECURITY ---
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# --- STATIC & MEDIA FILES ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media/'

# --- CELERY CONFIGURATION ---
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True
CELERY_BEAT_SCHEDULE = {
    'check-scheduled-broadcasts-every-minute': {
        'task': 'users.tasks.check_scheduled_broadcasts',
        'schedule': crontab(minute='*'),
    },
}

# --- EMAIL SETTINGS ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')

# --- SUMMERNOTE CONFIG ---
SUMMERNOTE_THEME = 'bs5'
SUMMERNOTE_CONFIG = {
    'iframe': {'height': '100%', 'width': '100%'},
    'summernote': {'width': '100%', 'styleWithSpan': False},
    'codemirror': {'lineWrapping': True},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

