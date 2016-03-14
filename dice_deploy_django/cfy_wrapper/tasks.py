from __future__ import absolute_import

from celery import shared_task
from celery.utils.log import get_task_logger

from cloudify_rest_client.client import CloudifyClient
from cloudify_rest_client.executions import Execution
from cloudify_rest_client.exceptions import (
    DeploymentEnvironmentCreationInProgressError,
    DeploymentEnvironmentCreationPendingError
)

from django.conf import settings

import os
import time

from .models import Blueprint

"""
Module with async tasks that should not block main process
"""


@shared_task
def debug_task():
    logger.info("##### Received DEBUG task #####")
    logger.info("IS_TEST_SETTINGS: %s" % settings.IS_TEST_SETTINGS)
    return "##### Received DEBUG task #####"


logger = get_task_logger('tasks')


def _get_cfy_client():
    if settings.MOCKUP_CFY:
        raise settings.MOCKUP_CFY

    return CloudifyClient(settings.CFY_MANAGER_URL)


def _wait_for_execution(client, execution):
    while execution.status not in Execution.END_STATES:
        time.sleep(settings.POOL_SLEEP_INTERVAL)
        execution = client.executions.get(execution.id)


def _update_state(blueprint, state):
    blueprint.refresh_from_db()
    blueprint.state = state.value
    blueprint.save()


def _run_execution(workflow_id, deployment_id):
    client = _get_cfy_client()
    blueprint = Blueprint.get(deployment_id)

    # Wait for environment to be prepared
    _update_state(blueprint, Blueprint.State.preparing_deploy)
    execution = next(e for e in client.executions.list(deployment_id)
                     if e.workflow_id == "create_deployment_environment")
    _wait_for_execution(client, execution)

    # Execute required workflow
    _update_state(blueprint, Blueprint.State.working)
    execution = client.executions.start(deployment_id, workflow_id)
    _wait_for_execution(client, execution)

    # We're done
    _update_state(blueprint, Blueprint.State.deployed)


@shared_task
def upload_blueprint(blueprint_id):
    blueprint = Blueprint.get(blueprint_id)
    client = _get_cfy_client()
    archive_path = os.path.join(settings.MEDIA_ROOT, blueprint.archive.name)

    logger.info("Uploading blueprint archive '{}'.".format(archive_path))

    # Next call will block until upload is finished (can take some time)
    client.blueprints.publish_archive(archive_path, blueprint.cfy_id)

    # Update blueprint status
    blueprint.refresh_from_db()
    blueprint.state = Blueprint.State.uploaded.value
    blueprint.save()


@shared_task
def create_deployment(blueprint_id):
    client = _get_cfy_client()

    logger.info("Creating deployment '{}'.".format(blueprint_id))

    # Next call will block until upload is finished (can take some time)
    client.deployments.create(blueprint_id, blueprint_id)

    # Update blueprint status
    blueprint = Blueprint.get(blueprint_id)
    blueprint.state = Blueprint.State.ready_to_deploy.value
    blueprint.save()


@shared_task
def install(blueprint_id):
    logger.info("Installing '{}'.".format(blueprint_id))
    _run_execution("install", blueprint_id)


@shared_task
def uninstall(blueprint_id):
    logger.info("Uninstalling '{}'.".format(blueprint_id))
    _run_execution("uninstall", blueprint_id)


@shared_task
def delete_deployment(blueprint_id):
    client = _get_cfy_client()

    logger.info("Deleting deployment '{}'.".format(blueprint_id))

    # Next call will block until upload is finished (can take some time)
    client.deployments.delete(blueprint_id)

    # Update blueprint status
    blueprint = Blueprint.get(blueprint_id)
    blueprint.state = Blueprint.State.uploaded.value
    blueprint.save()


@shared_task
def delete_blueprint(blueprint_id):
    client = _get_cfy_client()

    logger.info("Deleting blueprint '{}'.".format(blueprint_id))

    # Next call will block until upload is finished (can take some time)
    client.blueprints.delete(blueprint_id)

    # Delete all traces of this blueprint
    blueprint = Blueprint.get(blueprint_id)
    blueprint.archive.delete()
    blueprint.delete()
