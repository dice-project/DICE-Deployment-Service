from __future__ import absolute_import

from celery import shared_task
from celery.utils.log import get_task_logger

from . import utils

from cloudify_rest_client.executions import Execution

from django.conf import settings

import time

from .models import Blueprint, Input

"""
Module with async tasks that should not block main process
"""


@shared_task
def debug_task():
    logger.info("##### Received DEBUG task #####")
    logger.info("IS_TEST_SETTINGS: %s" % settings.IS_TEST_SETTINGS)
    return "##### Received DEBUG task #####"


logger = get_task_logger('tasks')


def _wait_for_execution(client, execution):
    while execution.status not in Execution.END_STATES:
        time.sleep(settings.POOL_SLEEP_INTERVAL)
        execution = client.executions.get(execution.id)


def _update_state(blueprint, state):
    blueprint.refresh_from_db()
    blueprint.state = state.value
    blueprint.save()


def _run_execution(workflow_id, deployment_id, blueprint_state_flow):
    blueprint = Blueprint.get(deployment_id)

    try:
        client = utils.get_cfy_client()

        # Wait for environment to be prepared
        _update_state(blueprint, blueprint_state_flow[0])
        execution = next(e for e in client.executions.list(deployment_id)
                         if e.workflow_id == "create_deployment_environment")
        _wait_for_execution(client, execution)

        # Execute required workflow
        _update_state(blueprint, blueprint_state_flow[1])
        execution = client.executions.start(deployment_id, workflow_id)
        _wait_for_execution(client, execution)

        # Capture deployment outputs
        blueprint.refresh_from_db()
        blueprint.outputs = get_outputs(blueprint)
        blueprint.save()

        # We're done
        _update_state(blueprint, blueprint_state_flow[2])
    except Exception, e:
        _handle_exception('_run_execution(%s)' % workflow_id, blueprint, e)


def _handle_exception(task_name, blueprint, exception_obj):
    logger.error('Exeption in %s: %s' % (task_name, exception_obj))
    blueprint.refresh_from_db()
    blueprint.state = Blueprint.State.error.value
    blueprint.save()
    raise exception_obj


@shared_task
def upload_blueprint(blueprint_id):
    blueprint = Blueprint.get(blueprint_id)
    try:
        client = utils.get_cfy_client()
        archive_path = blueprint.generate_archive()

        logger.info("Uploading blueprint archive '{}'.".format(archive_path))

        # Next call will block until upload is finished (can take some time)
        client.blueprints.publish_archive(archive_path, blueprint.cfy_id)

        # Update blueprint status
        blueprint.refresh_from_db()
        blueprint.state = Blueprint.State.uploaded.value
        blueprint.save()
    except Exception, e:
        _handle_exception('upload_blueprint', blueprint, e)


@shared_task
def create_deployment(blueprint_id):
    blueprint = Blueprint.get(blueprint_id)
    try:
        client = utils.get_cfy_client()

        logger.info("Creating deployment '{}'.".format(blueprint_id))

        # Next call will block until upload is finished (can take some time)
        client.deployments.create(
            blueprint_id,
            blueprint_id,
            inputs=Input.get_inputs_values_as_dict()
        )

        # Update blueprint status
        blueprint.refresh_from_db()
        blueprint.state = Blueprint.State.ready_to_deploy.value
        blueprint.save()
    except Exception, e:
        _handle_exception('create_deployment', blueprint, e)


@shared_task
def install(blueprint_id):
    logger.info("Installing '{}'.".format(blueprint_id))
    _run_execution(
        "install",
        blueprint_id,
        blueprint_state_flow=[
            Blueprint.State.preparing_deploy,
            Blueprint.State.working,
            Blueprint.State.deployed
        ]
    )


@shared_task
def uninstall(blueprint_id):
    logger.info("Uninstalling '{}'.".format(blueprint_id))

    # Update blueprint status
    blueprint = Blueprint.get(blueprint_id)
    blueprint.state = Blueprint.State.uninstalling.value
    blueprint.save()

    _run_execution(
        "uninstall",
        blueprint_id,
        blueprint_state_flow=[
            Blueprint.State.uninstalling,
            Blueprint.State.uninstalling,
            Blueprint.State.deleting_deployment
        ]
    )


@shared_task
def delete_deployment(blueprint_id):
    blueprint = Blueprint.get(blueprint_id)
    try:
        client = utils.get_cfy_client()

        logger.info("Deleting deployment '{}'.".format(blueprint_id))

        # Update blueprint status
        blueprint.refresh_from_db()
        blueprint.state = Blueprint.State.deleting_deployment.value
        blueprint.save()

        # Next call will block until upload is finished (can take some time)
        client.deployments.delete(blueprint_id)
    except Exception, e:
        _handle_exception('delete_deployment', blueprint, e)


@shared_task
def delete_blueprint(blueprint_id, delete_local=True):
    # Update blueprint status
    blueprint = Blueprint.get(blueprint_id)
    blueprint.state = Blueprint.State.deleting_deployment.value
    blueprint.save()

    try:
        client = utils.get_cfy_client()

        logger.info("Deleting blueprint '{}'. delete_local={}".format(blueprint_id, delete_local))

        # Next call fails sometimes if called to fast after deleting deployment.
        # Retry few times to solve the problem
        num_retries = 10
        for i in range(num_retries):
            try:
                client.blueprints.delete(blueprint_id)
                break
            except Exception, e:
                logger.warning("Could not delete blueprint from cfy, attempt: %d/%d. Error: %s" %
                               (i+1, num_retries, e))
                time.sleep(2)

        blueprint = Blueprint.get(blueprint_id)
        if delete_local:
            # Delete all traces of this blueprint
            blueprint.archive.delete()
            if bool(blueprint.yaml):
                blueprint.yaml.delete()
            blueprint.delete(keep_parents=True)
        else:
            blueprint.state = Blueprint.State.undeployed.value
            blueprint.save()
    except Exception, e:
        _handle_exception('delete_blueprint', blueprint, e)


def get_outputs(blueprint):
    client = utils.get_cfy_client()
    outputs_descriptions = client.deployments.get(blueprint.cfy_id).get('outputs', {})
    outputs = client.deployments.outputs.get(blueprint.cfy_id).get('outputs', {})

    for key, value in outputs.iteritems():
        outputs[key] = {
            'value': value,
            'description': outputs_descriptions.get(key, {}).get('description', '')
        }

    return outputs
