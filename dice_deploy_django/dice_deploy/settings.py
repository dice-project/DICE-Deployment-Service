"""
Django settings for dice_deploy project.

Generated by "django-admin startproject" using Django 1.8.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

import os

IS_TEST_SETTINGS = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = "np$u5a4u$rh-or%ibtladssbbrf26d(y4k+m_alh@r2hdebgiq"

DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = (
    "django.contrib.sessions",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_swagger",
    "cfy_wrapper.apps.CfyWrapper",
    "cfy_wrapper_gui",
    "rest_framework.authtoken",
    "django.contrib.admin"
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware'
)

API_DATE_FORMAT = '%Y-%m-%d'
API_TIME_FORMAT = '%H:%M:%S'
API_DT_FORMAT = '%sT%s' % (API_DATE_FORMAT, API_TIME_FORMAT)

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    "DATETIME_FORMAT": API_DT_FORMAT,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    )
}

ROOT_URLCONF = "dice_deploy.urls"
WSGI_APPLICATION = "dice_deploy.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Celery config
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_DEFAULT_QUEUE = 'dice_deploy'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'dice_deploy'
CELERY_TASK_ROUTES = {'dice_deploy': 'dice_deploy'}

# Cloudify settings
CFY_MANAGER_URL = "172.16.95.115"
CFY_MANAGER_PROTOCOL = "http"  # Other valid option is "https"
CFY_MANAGER_USERNAME = "username"
CFY_MANAGER_PASSWORD = "password"
CFY_MANAGER_CACERT = None  # Path to self-signed certificate if needed
POOL_SLEEP_INTERVAL = 3  # In seconds

# File upload storage
MEDIA_ROOT = os.path.join(BASE_DIR, "uploads")

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s "
                      "[%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'app.log',
            'formatter': 'verbose',
        },
        'file_tasks': {
            'class': 'logging.FileHandler',
            'filename': 'tasks.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'views': {
            'handlers': ['console', 'file'],
            'propagate': False,
            'level': 'DEBUG',
        },
        'tasks': {
            'handlers': ['console', 'file_tasks'],
            'propagate': False,
            'level': 'DEBUG',
        },
    },
}

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# angular configuration
ANGULAR_ENDPOINT = '/'

SWAGGER_SETTINGS = {
    "USE_SESSION_AUTH": False,
}

# Local overrides
try:
    from dice_deploy.local_settings import *  # noqa: F401,F403
except ImportError:
    pass
