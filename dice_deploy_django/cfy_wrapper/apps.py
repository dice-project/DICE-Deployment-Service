from django.conf import settings
from django.apps import AppConfig

import os


class CfyWrapper(AppConfig):
    name = "cfy_wrapper"
    verbose_name = "Cloudify wrapper"

    def ready(self):
        from . import signals  # noqa

        try:
            os.makedirs(settings.MEDIA_ROOT)
        except OSError:
            if not os.path.isdir(settings.MEDIA_ROOT):
                raise
