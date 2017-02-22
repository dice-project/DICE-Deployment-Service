from __future__ import absolute_import

from celery import Task, shared_task, chain
from celery.utils.log import get_task_logger

from . import utils
from .models import Blueprint, Container, Input

from cloudify_rest_client import exceptions, executions
from concurrency.exceptions import RecordModifiedError

from django.conf import settings

import time

import requests


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


class Job(Task):
    """
    Custom celery tasks that takes care of error handling. This should be used
    as a base for all tasks.

    IMPORTANT! Make sure that all tasks receive container_id as a last
    argument. We need this information in order to properly release container
    and log error messages.
    """

    autoretry_excs = (requests.Timeout, requests.ConnectionError)

    max_retries = None
    default_retry_delay = 10

    def __init__(self):
        self.client = utils.get_cfy_client()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        container_id = args[-1]
        logger.error("Operation in container {} failed.".format(container_id))

        blueprint = Container.get(container_id).blueprint
        blueprint.state = -abs(blueprint.state)
        blueprint.save()

        blueprint.log_error(str(exc))
        logger.error(str(exc))

        release_container(container_id)


def _get_blueprint_with_state(container_id, state):
    blueprint = Container.get(container_id).blueprint
    blueprint.state = state
    blueprint.save()
    return blueprint, blueprint.cfy_id


@shared_task(bind=True, base=Job, autoretry_for=Job.autoretry_excs,
             retry_kwargs=dict(max_retries=5))
def upload_blueprint(task, container_id):
    blueprint, id = _get_blueprint_with_state(
        container_id, Blueprint.State.uploading_to_cloudify
    )

    logger.info("Creating archive for '{}'.".format(id))
    archive = blueprint.pack()

    logger.info("Uploading blueprint archive '{}'.".format(archive))
    task.client.blueprints.publish_archive(archive, id)


@shared_task(bind=True, base=Job, autoretry_for=Job.autoretry_excs,
             retry_kwargs=dict(max_retries=5))
def create_deployment(task, container_id):
    blueprint, id = _get_blueprint_with_state(
        container_id, Blueprint.State.preparing_deployment
    )

    logger.info("Gathering inputs for '{}'.".format(id))
    inputs = blueprint.prepare_inputs()

    logger.info("Creating deployment '{}'.".format(id))
    task.client.deployments.create(id, id, inputs=inputs)
    blueprint.state = Blueprint.State.prepared_deployment
    blueprint.save()

    executions = task.client.executions.list(
        id, workflow_id="create_deployment_environment"
    )
    if len(executions) < 1:
        raise Exception("Deployment creation execution did not start.")
    elif len(executions) > 1:
        raise Exception("More than one deployment creation execution started.")

    return executions[0].id


@shared_task(bind=True, base=Job, autoretry_for=Job.autoretry_excs,
             retry_kwargs=dict(countdown=3))
def wait_for_execution(task, execution_id, allow_missing, container_id):
    # This can (and most likely will) happen on deployment deletion, since
    # delete_deployment_environment is almost instantaneous on most platforms
    # and will be long gone when we query for it.
    if execution_id is None:
        return

    logger.info("Waiting for execution {}.".format(execution_id))

    try:
        execution = task.client.executions.get(execution_id)
        while execution.status not in executions.Execution.END_STATES:
            time.sleep(settings.POOL_SLEEP_INTERVAL)
            execution = task.client.executions.get(execution_id)
    except exceptions.CloudifyClientError as e:
        if allow_missing and e.status_code == 404:
            logger.info("Execution '{}' succeeded.".format(execution_id))
            return
        raise

    if execution.status != executions.Execution.TERMINATED:
        msg = "Execution '{}' terminated abnormally.".format(execution_id)
        raise Exception(msg)


@shared_task(bind=True, base=Job, autoretry_for=Job.autoretry_excs,
             retry_kwargs=dict(max_retries=5))
def install_blueprint(task, container_id):
    blueprint, id = _get_blueprint_with_state(
        container_id, Blueprint.State.installing
    )

    logger.info("Scheduling install on deployment '{}'.".format(id))
    return task.client.executions.start(id, "install").id


@shared_task(bind=True, base=Job, autoretry_for=Job.autoretry_excs,
             retry_kwargs=dict(max_retries=5))
def fetch_blueprint_outputs(task, container_id):
    # TODO: If we cannot get outputs, something is wrong with connection, but
    # we certainly would not like to fail run for this. Needs more thought,
    # leave only happy path in for now.
    blueprint, id = _get_blueprint_with_state(
        container_id, Blueprint.State.fetching_outputs
    )

    logger.info("Collecting outputs for blueprint '{}'.".format(id))
    descs = task.client.deployments.get(id).get("outputs", {})
    outs = task.client.deployments.outputs.get(id).get("outputs", {})

    for key, value in outs.items():
        outs[key] = {
            "value": value,
            "description": descs.get(key, {}).get("description", "")
        }

    blueprint.outputs = outs
    blueprint.state = Blueprint.State.deployed
    blueprint.save()


@shared_task(bind=True, base=Job, autoretry_for=Job.autoretry_excs,
             retry_kwargs=dict(max_retries=5))
def uninstall_blueprint(task, container_id):
    blueprint, id = _get_blueprint_with_state(
        container_id, Blueprint.State.uninstalling
    )

    logger.info("Scheduling uninstall on deployment '{}'.".format(id))
    return task.client.executions.start(id, "uninstall").id


@shared_task(bind=True, base=Job, autoretry_for=Job.autoretry_excs,
             retry_kwargs=dict(max_retries=5))
def delete_deployment(task, container_id):
    blueprint, id = _get_blueprint_with_state(
        container_id, Blueprint.State.deleting_deployment
    )

    logger.info("Scheduling deployment '{}' deletion.".format(id))
    task.client.deployments.delete(id)

    try:
        executions = task.client.executions.list(
            id, workflow_id="delete_deployment_environment"
        )
    except exceptions.CloudifyClientError as e:
        if e.status_code == 404:
            return None

    if len(executions) < 1:
        raise Exception("Deployment deletion did not start.")
    elif len(executions) > 1:
        raise Exception("More than one deployment deletion started.")

    return executions[0].id


@shared_task(bind=True, base=Job, autoretry_for=Job.autoretry_excs,
             retry_kwargs=dict(max_retries=5))
def delete_blueprint(task, container_id):
    blueprint, id = _get_blueprint_with_state(
        container_id, Blueprint.State.deleting_from_cloudify
    )

    logger.info("Deleting blueprint '{}'.".format(id))
    task.client.blueprints.delete(id)
    blueprint.state = Blueprint.State.present
    blueprint.save()


@shared_task(base=Job)
def process_container_queue(container_id):
    logger.info("Switching container blueprint")
    container = Container.get(container_id)
    if container.blueprint and container.blueprint != container.queue:
        container.blueprint.delete()
    container.blueprint = container.queue
    container.queue = None
    container.save()


@shared_task(base=Job)
def release_container(container_id):
    logger.info("Releasing container {}".format(container_id))
    container = Container.get(container_id)
    container.busy = False
    container.save()


@shared_task(base=Job, autoretry_for=Job.autoretry_excs,
             retry_kwargs=dict(max_retries=5))
def register_app(container_id):
    blueprint, id = _get_blueprint_with_state(
        container_id, Blueprint.State.deleting_from_cloudify
    )

    logger.info("Registering application.")
    try:
        dmon_address = Input.objects.get(key="dmon_address")
    except Input.DoesNotExist:
        blueprint.log_error("Missing input: 'dmon_address'. "
                            "Cannot register application with dmon.")
        return

    url = "http://{}/dmon/v1/overlord/application/{}"
    response = requests.put(url.format(dmon_address.value, id))
    if response.status_code != 200:
        msg = "Application registration failed: '{}'"
        blueprint.log_error(msg.format(response.text))


def _get_deploy_pipe(container, register_app):
    if container.queue is None:
        return []

    id = container.cfy_id
    pipe = [
        upload_blueprint.si(id),
        create_deployment.si(id),
        wait_for_execution.s(False, id),
        install_blueprint.si(id),
        wait_for_execution.s(False, id),
        fetch_blueprint_outputs.si(id),
    ]
    if register_app:
        pipe.insert(1, register_app.si(id))

    return pipe


def _get_undeploy_pipe(container):
    if container.blueprint is None:
        return []

    # Simulate C's switch statement with fall-through
    index_map = {
        Blueprint.State.present:                 5,
        Blueprint.State.uploading_to_cloudify:   5,
        Blueprint.State.preparing_deployment:    4,
        Blueprint.State.prepared_deployment:     2,
        Blueprint.State.installing:              0,
        Blueprint.State.fetching_outputs:        0,

        Blueprint.State.deployed:                0,

        Blueprint.State.uninstalling:            0,
        Blueprint.State.deleting_deployment:     2,
        Blueprint.State.deleting_from_cloudify:  4,
    }
    id = container.cfy_id
    pipe = [
        uninstall_blueprint.si(id),
        wait_for_execution.s(False, id),
        delete_deployment.si(id),
        wait_for_execution.s(True, id),
        delete_blueprint.si(id),
    ]
    index = index_map[abs(container.blueprint.state)]
    return pipe[index:]


# This should be the only entry point into celery
def sync_container(container, blueprint, register_app):
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
         - commit changes [success, msg = sync_container(c, None)]

     3. Redeploying same blueprint:
         - find container [c = Container.get(uuid_of_container)]
         - commit changes [success, msg = sync_container(c, c.blueprint)]

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
    pipe.extend(_get_deploy_pipe(container, register_app))
    pipe.append(release_container.si(container.cfy_id))

    chain(*pipe).apply_async()
    return True, "All OK"
