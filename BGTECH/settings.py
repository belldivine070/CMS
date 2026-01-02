"""
Django settings for BGTECH project.
Production-ready for Render
"""

from pathlib import Path
import os
from celery.schedules import crontab
import dj_database_url

# --------------------------------------------------
# BASE DIR
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------
# SECURITY
# --------------------------------------------------
SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.onrender.com',
]


# --------------------------------------------------
# APPLICATIONS
# --------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'django_summernote',
    'widget_tweaks',

    # Local apps
    'users.apps.UsersConfig',
    'portech.apps.PortechConfig',
]


# --------------------------------------------------
# MIDDLEWARE  (ORDER IS CRITICAL)
# --------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# --------------------------------------------------
# URLS & WSGI
# --------------------------------------------------
ROOT_URLCONF = 'BGTECH.urls'

WSGI_APPLICATION = 'BGTECH.wsgi.application'


# --------------------------------------------------
# TEMPLATES
# --------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'users.context_processors.app_settings_processor',
            ],
        },
    },
]


# --------------------------------------------------
# DATABASE (Render PostgreSQL)
# --------------------------------------------------
DATABASES = {

    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

    #'default': dj_database_url.config(
     #   default=os.environ.get('DATABASE_URL'),
     #   conn_max_age=600,
     #   ssl_require=True,
    )
}


# --------------------------------------------------
# AUTH
# --------------------------------------------------
AUTH_USER_MODEL = 'users.CustomUser'

LOGIN_URL = '/bg-admin/login/'
LOGOUT_REDIRECT_URL = '/bg-admin/login/'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]


# --------------------------------------------------
# PASSWORD VALIDATION
# --------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --------------------------------------------------
# INTERNATIONALIZATION
# --------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# --------------------------------------------------
# STATIC & MEDIA (RENDER FIX)
# --------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_STORAGE = (
    'whitenoise.storage.CompressedManifestStaticFilesStorage'
)

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# --------------------------------------------------
# DEFAULT PK
# --------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --------------------------------------------------
# SUMMERNOTE
# --------------------------------------------------
X_FRAME_OPTIONS = 'SAMEORIGIN'

SUMMERNOTE_THEME = 'bs5'

SUMMERNOTE_CONFIG = {
    'iframe': {
        'height': '100%',
        'width': '100%',
    },
    'summernote': {
        'width': '100%',
        'styleWithSpan': False,
        'bodyClass': 'summernote-editable-area',
    },
    'codemirror': {
        'lineWrapping': True,
        'lineNumbers': False,
    },
}


# --------------------------------------------------
# EMAIL (GMAIL SMTP – RENDER SAFE)
# --------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False

EMAIL_HOST_USER = '{{ OFFICIAL_EMAIL }}' # os.environ.get('OFFICIAL_EMAIL')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# --------------------------------------------------
# CELERY (REDIS ON RENDER)
# --------------------------------------------------
CELERY_BROKER_URL = os.environ.get(
    'REDIS_URL', 'redis://localhost:6379/0'
)

CELERY_RESULT_BACKEND = CELERY_BROKER_URL
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








    
