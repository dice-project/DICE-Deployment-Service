from __future__ import absolute_import

import os
from celery import Celery

# This is set here since django.conf import needs to have this set
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dice_deploy.settings")

from django.conf import settings  # noqa: E402

app = Celery("dice_deploy")
app.config_from_object("django.conf:settings")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
