from django.db.models.signals import post_init, post_save, pre_delete
from django.dispatch import receiver
from django.conf import settings

from rest_framework.authtoken.models import Token

from .models import Blueprint

import shutil
import os


@receiver(post_init, sender=Blueprint)
def create_blueprint_folder(instance, **_):
    """
    This method can be called multiple times, so we need to make sure we
    create folder only the first time.
    """
    if not os.path.isdir(instance.content_folder):
        os.mkdir(instance.content_folder)


@receiver(pre_delete, sender=Blueprint)
def delete_blueprint_folder(instance, **_):
    shutil.rmtree(instance.content_folder, ignore_errors=True)
    try:
        os.unlink(instance.content_tar)
    except OSError:
        pass


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
