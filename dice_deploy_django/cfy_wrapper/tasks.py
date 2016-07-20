from __future__ import absolute_import

from celery import shared_task, chain
from celery.utils.log import get_task_logger

from . import utils
from .models import Blueprint, Container

from cloudify_rest_client import exceptions, executions
from concurrency.exceptions import RecordModifiedError

from django.conf import settings

import time


"""
Module with async tasks that should not block main process.

This module is pretty hairy because we need to handle quite a few different
scenarios that can happen during cloudify run. Each phase of cloudify run is
encapsulated in a celery task. Tasks are then chained together, with proper
error handling and chain termination added for error conditions.

There is a single function in this module that should be used by external
code: sync_container. This function takes care of locking the container that
prevents concurrent executions of multiple tasks in single container.
"""

logger = get_task_logger("tasks")


@shared_task(bind=True)
def debug_task(task):
    logger.info("##### Received DEBUG task #####")
    logger.info("IS_TEST_SETTINGS: %s" % settings.IS_TEST_SETTINGS)
    return "##### Received DEBUG task #####"


def _update_state(blueprint_id, state, success=True):
    blueprint = Blueprint.get(blueprint_id)
    blueprint.state = state if success else -state
    blueprint.save()


def _cancel_chain_execution(task, container_id):
    task.request.callbacks = None
    release_container(container_id)


def _wait_for_execution(client, execution, on_deleted=False):
    """
    This function waits for cloudify execution to reach terminal state. It
    returns true when cloudify executions terminates in success state.

    It is possible to override return value in the case of deleted execution
    (such as when we delete deployment environment and all executions get
    deleted too).
    """

    success = False
    try:
        while execution.status not in executions.Execution.END_STATES:
            time.sleep(settings.POOL_SLEEP_INTERVAL)
            execution = client.executions.get(execution.id)
        success = execution.status == executions.Execution.TERMINATED
    except exceptions.CloudifyClientError as e:
        success = on_deleted if e.status_code == 404 else False
    return success


def _run_workflow(task, workflow_id, container_id, blueprint_id,
                  start_state, end_state):
    _update_state(blueprint_id, start_state)
    client = utils.get_cfy_client()
    success = False

    try:
        execution = client.executions.start(blueprint_id, workflow_id)
        success = _wait_for_execution(client, execution)
    except exceptions.CloudifyClientError:
        _update_state(blueprint_id, start_state, False)
    else:
        _update_state(blueprint_id, end_state, success)

    if not success:
        _cancel_chain_execution(task, container_id)
    return success


@shared_task(bind=True)
def upload_blueprint(task, container_id):
    logger.info("Uploading archive from container '{}'.".format(container_id))
    id = Container.get(container_id).blueprint.cfy_id

    _update_state(id, Blueprint.State.uploading_to_cloudify)
    client = utils.get_cfy_client()

    logger.info("Creating archive for '{}'.".format(id))
    blueprint = Blueprint.get(id)
    archive = blueprint.pack()

    try:
        logger.info("Uploading blueprint archive '{}'.".format(archive))
        client.blueprints.publish_archive(archive, id)
        _update_state(id, Blueprint.State.uploaded_to_cloudify)
        logger.info("Blueprint '{}' upload succeeded.".format(id))
    except exceptions.CloudifyClientError:
        _update_state(id, Blueprint.State.uploading_to_cloudify, False)
        logger.info("Blueprint '{}' upload failed.".format(id))
        _cancel_chain_execution(task, container_id)


@shared_task(bind=True)
def create_deployment(task, container_id):
    id = Container.get(container_id).blueprint.cfy_id

    _update_state(id, Blueprint.State.preparing_deployment)
    client = utils.get_cfy_client()
    success = False

    logger.info("Creating deployment '{}'.".format(id))
    try:
        client.deployments.create(id, id)
    except exceptions.CloudifyClientError:
        _update_state(id, Blueprint.State.preparing_deployment, False)
        _cancel_chain_execution(task, container_id)
        logger.info("Deployment '{}' creation failed.".format(id))
        return

    logger.info("Waiting for deployment environment to initialize.")
    try:
        execution = next(e for e in client.executions.list(id)
                         if e.workflow_id == "create_deployment_environment")
    except exceptions.CloudifyClientError:
        _update_state(id, Blueprint.State.prepared_deployment, False)
        _cancel_chain_execution(task, container_id)
        logger.info("Deployment '{}' creation failed.".format(id))
        return

    success = _wait_for_execution(client, execution)
    _update_state(id, Blueprint.State.prepared_deployment, success)
    if success:
        logger.info("Deployment '{}' creation succeeded.".format(id))
    else:
        _cancel_chain_execution(task, container_id)
        logger.info("Deployment '{}' creation failed.".format(id))


@shared_task(bind=True)
def install_blueprint(task, container_id):
    id = Container.get(container_id).blueprint.cfy_id

    logger.info("Running install on deployment '{}'.".format(id))
    success = _run_workflow(task, "install", container_id, id,
                            Blueprint.State.installing,
                            Blueprint.State.installed)
    msg = "Install on deployment '{}' {}."
    logger.info(msg.format(id, "succeeded" if success else "failed"))


@shared_task(bind=True)
def fetch_blueprint_outputs(task, container_id):
    # TODO: If we cannot get outputs, something is wrong with connection, but
    # we certainly would not like to fail run for this. Needs more thought,
    # leave only happy path in for now.
    id = Container.get(container_id).blueprint.cfy_id

    _update_state(id, Blueprint.State.fetching_outputs)
    logger.info("Collecting outputs for blueprint '{}'.".format(id))

    client = utils.get_cfy_client()
    descs = client.deployments.get(id).get("outputs", {})
    outs = client.deployments.outputs.get(id).get("outputs", {})

    for key, value in outs.iteritems():
        outs[key] = {
            "value": value,
            "description": descs.get(key, {}).get("description", "")
        }

    blueprint = Blueprint.get(id)
    blueprint.outputs = outs
    blueprint.save()
    _update_state(id, Blueprint.State.fetched_outputs)


@shared_task(bind=True)
def uninstall_blueprint(task, container_id):
    id = Container.get(container_id).blueprint.cfy_id

    logger.info("Running uninstall on deploment '{}'.".format(id))
    success = _run_workflow(task, "uninstall", container_id, id,
                            Blueprint.State.uninstalling,
                            Blueprint.State.uninstalled)
    msg = "Uninstall on deployment '{}' {}."
    logger.info(msg.format(id, "succeeded" if success else "failed"))


@shared_task(bind=True)
def delete_deployment(task, container_id):
    """
    This task is one giant can of worms, because there is about a schmillion
    ways things can terminate when we delete deployment. Most of them will
    never be encountered (since most platforms behave quite reasonably), but
    in order to be on the safe side, we handle just about anything here.

    Happy path: Call delete, when back from delete, deployment is gone.
    Sad path: Call delete, when back from delete, deployment is not gone. Now
              wait for this deployment to terminate and keep fingers crossed
              that things really terminate.
    """
    id = Container.get(container_id).blueprint.cfy_id

    _update_state(id, Blueprint.State.deleting_deployment)
    client = utils.get_cfy_client()

    logger.info("Deleting deployment '{}'.".format(id))
    try:
        client.deployments.delete(id)
    except exceptions.CloudifyClientError:
        _update_state(id, Blueprint.State.deleting_deployment, False)
        _cancel_chain_execution(task, container_id)
        logger.info("Deployment '{}' deletion failed.".format(id))
        return

    logger.info("Waiting for deployment environment to vanish.")
    try:
        execution = next(e for e in client.executions.list(id)
                         if e.workflow_id == "delete_deployment_environment")
    except exceptions.CloudifyClientError as e:
        if e.status_code == 404:
            # Happy path
            _update_state(id, Blueprint.State.deleted_deployment)
            logger.info("Deployment '{}' deletion succeeded.".format(id))
        else:
            _update_state(id, Blueprint.State.deleted_deployment, False)
            _cancel_chain_execution(task, container_id)
            logger.info("Deployment '{}' deletion failed.".format(id))
        return

    # Sad path
    success = _wait_for_execution(client, execution, on_delete=True)
    _update_state(id, Blueprint.State.deleted_deployment, success)
    if success:
        logger.info("Deployment '{}' deletion succeeded.".format(id))
    else:
        _cancel_chain_execution(task, container_id)
        logger.info("Deployment '{}' deletion failed.".format(id))


@shared_task(bind=True)
def delete_blueprint(task, container_id):
    id = Container.get(container_id).blueprint.cfy_id

    _update_state(id, Blueprint.State.deleting_from_cloudify)
    client = utils.get_cfy_client()

    logger.info("Deleting blueprint '{}'.".format(id))
    try:
        client.blueprints.delete(id)
        _update_state(id, Blueprint.State.present)
        logger.info("Blueprint '{}' deletion succeeded.".format(id))
    except exceptions.CloudifyClientError:
        _update_state(id, Blueprint.State.deleting_from_cloudify, False)
        _cancel_chain_execution(task, container_id)
        logger.info("Blueprint '{}' deletion failed.".format(id))


@shared_task
def process_container_queue(container_id):
    logger.info("Switching container blueprint")
    container = Container.get(container_id)
    if container.blueprint and container.blueprint != container.queue:
        container.blueprint.delete()
    container.blueprint = container.queue
    container.queue = None
    container.save()


@shared_task
def release_container(container_id):
    container = Container.get(container_id)
    container.busy = False
    container.save()


def _get_deploy_pipe(container):
    if container.queue is None:
        return []

    id = container.cfy_id
    return [
        upload_blueprint.si(id),
        create_deployment.si(id),
        install_blueprint.si(id),
        fetch_blueprint_outputs.si(id),
    ]


def _get_undeploy_pipe(container):
    if container.blueprint is None:
        return []

    # Simulate C's switch statement with fall-through
    index_map = {
        Blueprint.State.present:                 3,
        Blueprint.State.uploading_to_cloudify:   3,
        Blueprint.State.uploaded_to_cloudify:    2,
        Blueprint.State.preparing_deployment:    2,
        Blueprint.State.prepared_deployment:     1,
        Blueprint.State.installing:              1,
        Blueprint.State.installed:               0,
        Blueprint.State.fetching_outputs:        0,
        Blueprint.State.fetched_outputs:         0,
        Blueprint.State.uninstalling:            0,
        Blueprint.State.uninstalled:             0,
        Blueprint.State.deleting_deployment:     1,
        Blueprint.State.deleted_deployment:      1,
        Blueprint.State.deleting_from_cloudify:  2,
    }
    id = container.cfy_id
    pipe = [
        uninstall_blueprint.si(id),
        delete_deployment.si(id),
        delete_blueprint.si(id),
    ]
    index = index_map[container.blueprint.state]
    return pipe[index:]


# This should be the only entry point into celery
def sync_container(container, blueprint):
    """
    Function that should be used to get container into requested state.

    This function will update container status in race-free fashion and either
    return (True, msg) if the synchronization has been scheduled successfully
    or (False, msg) if the synchronization cannot be executed. Msg will
    contain the reason of failure.

    Internally, each container has two blueprint slots: one for currently
    deployed blueprint and one for queued blueprint. On each synchronization,
    this function deletes deployment of the first blueprint, removes blueprint
    and then deploys queued blueprint. It takes care to properly handle
    redeployments and None blueprints, but this is basically all there is to
    it.

    Some examples of how to handle common scenarios using this function

     1. Deploying blueprint in empty container:
         - create empty container [c = Container()]
         - create new blueprint   [b = Blueprint()]
         - commit changes         [success, msg = sync_container(c, b)]

     2. Deleting existing deployment:
         - find container [c = Container.get(uuid_of_container)]
         - commit changes [success, msg = sync_container(c, b)]

     3. Redeploying same blueprint:
         - find container [c = Container.get(uuid_of_container)]
         - commit changes [success, msg = sync_container(c, b)]

     4. Replacing blueprint in container:
         - find container       [c = Container.get(uuid_of_container)]
         - create new blueprint [b = Blueprint()]
         - commit changes       [success, msg = sync_container(c, b)]
    """
    busy_msg = "Container '{}' is busy.".format(container.id)

    if container.busy:
        return False, busy_msg

    # Try to acquire exclusive access to container
    container.busy = True
    try:
        container.save()
    except RecordModifiedError:
        return False, busy_msg

    # We have sole ownership over this container from now

    # Remove any failed remnants in queue and enqueue new blueprint
    if container.queue:
        container.queue.delete()
    container.queue = blueprint
    container.save()

    # Construct task sequence and execute it
    pipe = []
    pipe.extend(_get_undeploy_pipe(container))
    pipe.append(process_container_queue.si(container.cfy_id))
    pipe.extend(_get_deploy_pipe(container))
    pipe.append(release_container.si(container.cfy_id))

    chain(*pipe).apply_async()
    return True, "All OK"
