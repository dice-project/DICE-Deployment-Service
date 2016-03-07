from __future__ import absolute_import

import os

# This is set here since django.conf import needs to have this set
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dice_deploy.settings")

from celery import Celery
from django.conf import settings

app = Celery(settings.CELERY_APP_NAME)
app.config_from_object("django.conf:settings")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
