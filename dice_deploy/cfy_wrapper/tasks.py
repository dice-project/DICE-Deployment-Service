from __future__ import absolute_import

from celery import shared_task
from celery.utils.log import get_task_logger

from cloudify_rest_client.client import CloudifyClient
from django.conf import settings

import os

from .models import Blueprint

"""
Module with async tasks that should not block main process
"""

logger = get_task_logger(__name__)

def _get_cfy_client():
    return CloudifyClient(settings.CFY_MANAGER_URL)

@shared_task
def upload_blueprint(blueprint_id):
    blueprint = Blueprint.objects.get(pk = blueprint_id)
    client = _get_cfy_client()
    archive_path = os.path.join(settings.MEDIA_ROOT, blueprint.archive.name)

    logger.info("Uploading blueprint archive '{}'.".format(archive_path))

    # Next call will block until upload is finished (can take some time)
    client.blueprints.publish_archive(archive_path, str(blueprint_id))

    # Update blueprint status
    blueprint.refresh_from_db()
    blueprint.state = Blueprint.State.uploaded.value
    blueprint.save()

@shared_task
def create_deployment(blueprint_id):
    blueprint = Blueprint.objects.get(pk = blueprint_id)
    client = _get_cfy_client()

    logger.info("Creating deployment '{}'.".format(blueprint_id))

    # Next call will block until upload is finished (can take some time)
    client.deployments.create(str(blueprint_id), str(blueprint_id))

    # Update blueprint status
    blueprint.refresh_from_db()
    blueprint.status = Blueprint.State.ready_to_deploy.value
    blueprint.save()

@shared_task
def install(blueprint_id):
    # TODO: Execute install workflow
    pass

@shared_task
def uninstall(blueprint_id):
    # TODO: Execute uninstall
    pass

@shared_task
def delete_deployment(blueprint_id):
    # TODO: Execute deployments delete -d id
    pass

@shared_task
def delete_blueprint(blueprint_id):
    # TODO: Execute blueprints delete -b id
    pass
