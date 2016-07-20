import logging
import time
import sys
import os

from cloudify_rest_client.exceptions import CloudifyClientError
import utils

# Setup logging
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s <%(name)s> %(message)s"
)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

logger = logging.getLogger("teardown")
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)


def uninstall(deployment_id):
    logger.info("Uninstalling deployment service.")
    exec_client = utils.get_cfy_client().executions

    executions = exec_client.list(deployment_id=deployment_id)
    installs = [e for e in executions if e.workflow_id == "install"]
    if len(installs) == 0:
        logger.info("No installation present. Skipping.")
        return

    logger.info("Running uninstall workflow.")
    execution = exec_client.start(deployment_id=deployment_id,
                                  workflow_id="uninstall")
    while execution.status not in utils.TERMINAL_STATUSES:
        time.sleep(5)
        execution = exec_client.get(execution_id=execution.id)
    logger.info("Uninstall finished.")


def delete_deployment(deployment_id):
    logger.info("Deleting deployment.")
    depl_client = utils.get_cfy_client().deployments

    try:
        depl_client.get(deployment_id)
    except CloudifyClientError as e:
        logger.info("No deployment. Skipping.")
        return

    attempts = 20
    while attempts > 0:
        try:
            depl_client.delete(deployment_id)
            break
        except CloudifyClientError as e:
            attempts -= 1
            logger.warning("Failed deleting the deployment. {} attempts left. "
                           "{}".format(attempts, e))
            time.sleep(5)

    if attempts == 0:
        logger.error("Failed to delete deployment.")
        sys.exit(1)


def delete_blueprint(blueprint_id):
    logger.info("Deleting blueprint.")
    blue_client = utils.get_cfy_client().blueprints

    try:
        blue_client.delete(blueprint_id)
    except CloudifyClientError:
        pass


def teardown(test_state_file):
    deployment_id = os.path.basename(test_state_file)

    uninstall(deployment_id)
    delete_deployment(deployment_id)
    delete_blueprint(deployment_id)


if __name__ == "__main__":
    teardown(sys.argv[1])
