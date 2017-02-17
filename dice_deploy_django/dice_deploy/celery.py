from __future__ import absolute_import

import os
from celery import Celery

# This is set here for celery command
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dice_deploy.settings")

app = Celery("dice_deploy")
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
