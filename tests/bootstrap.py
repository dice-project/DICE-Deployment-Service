import subprocess
import logging
import time
import sys
import os
import re

import requests
import utils


# Setup logging
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s <%(name)s> %(message)s"
)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

logger = logging.getLogger("bootstrap")
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)

# Exit statuses
EXIT_SUCCESS = 0
EXIT_NOTHING_DONE_FAIL = 1
EXIT_RECOVERABLE_FAIL = 2
EXIT_COMPLETE_FAIL = 3


def non_terminal_executions(executions):
    return [e for e in executions if e.status not in utils.TERMINAL_STATUSES]


def get_outputs(deployment_id):
    depl_client = utils.get_cfy_client().deployments
    outputs = depl_client.outputs.get(deployment_id=deployment_id)
    return outputs["outputs"]


def shell_call(*cmd, **kwargs):
    logger.debug("Running cmd={}".format(cmd))
    return subprocess.Popen(cmd, **kwargs)


def wait_for_process(proc):
    retcode = proc.poll()
    while retcode is None:
        logger.debug(proc.stdout.read())
        logger.debug(proc.stderr.read())
        time.sleep(2)
        retcode = proc.poll()


def check(condition, msg):
    if not condition:
        logger.error(msg)
        sys.exit(EXIT_RECOVERABLE_FAIL)


def check_config():
    logger.info("Checking configuration")
    vars = ("TEST_CFY_MANAGER", "TEST_CFY_MANAGER_USERNAME",
            "TEST_CFY_MANAGER_PASSWORD")
    missing = [v for v in vars if v not in os.environ or os.environ[v] == ""]
    if len(missing) > 0:
        logger.error("Please define next variable(s): {}".format(missing))
        sys.exit(EXIT_NOTHING_DONE_FAIL)


def prepare_cfy_env():
    logger.info("Preparing environment variables")
    cfy_env = os.environ.copy()
    cfy_env["CLOUDIFY_USERNAME"] = os.environ["TEST_CFY_MANAGER_USERNAME"]
    cfy_env["CLOUDIFY_PASSWORD"] = os.environ["TEST_CFY_MANAGER_PASSWORD"]
    return cfy_env


def prepare_cfy_sandbox(cfy_env):
    logger.info("Initializing cfy sandbox using {} as a server".format(
        os.environ["TEST_CFY_MANAGER"]
    ))
    proc = shell_call("cfy", "use", "-t", os.environ["TEST_CFY_MANAGER"],
                      env=cfy_env, cwd=utils.BASE_DIR)
    retcode = proc.wait()
    if retcode != 0:
        logger.error(
            "Failed to connect to the Cloudify manager. Check the "
            "TEST_CFY_MANAGER, TEST_CFY_MANAGER_USERNAME and "
            "TEST_CFY_MANAGER_PASSWORD environment variables."
        )
        sys.exit(EXIT_NOTHING_DONE_FAIL)


def execute_up(platform, deployment_id, cfy_env):
    logger.info("Running ./up.sh {} {}".format(platform, deployment_id))
    proc = shell_call("./up.sh", platform, deployment_id,
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                      env=cfy_env, cwd=os.path.dirname(utils.BASE_DIR))
    wait_for_process(proc)
    logger.info("Done running ./up.sh")


def wait_for_installation(deployment_id):
    logger.info("Waiting for installation execution to finish.")

    exec_client = utils.get_cfy_client().executions
    executions = exec_client.list(deployment_id=deployment_id)
    non_term_executions = non_terminal_executions(executions)
    if len(non_term_executions) == 0:
        return

    logger.info("Installation still running. Waiting for termination.")
    # we have already waited for 15 minutes. 10 minutes more should
    # be more than enough
    sleep_time = 5
    attempts = 120
    while len(non_term_executions) > 0 and attempts > 0:
        time.sleep(sleep_time)
        executions = exec_client.list(deployment_id=deployment_id)
        non_term_executions = non_terminal_executions(executions)
        attempts -= 1

    if len(non_term_executions) == 0:
        return

    logger.info("Installation has been running too long. Cancelling.")
    exec_client.cancel(execution_id=non_term_executions[0].id)
    # now wait a bit until it is really cancelled
    attempts = 24
    execution = exec_client.get(execution_id=non_term_executions[0].id)
    while execution.status != "cancelled" and attempts > 0:
        time.sleep(sleep_time)
        attempts -= 1
        execution = exec_client.get(execution_id=execution.id)

    if execution.status == "cancelled":
        logger.error("The installation did not finish in due time.")
        sys.exit(EXIT_RECOVERABLE_FAIL)

    logger.error("Installation cannot be cancelled.")
    sys.exit(EXIT_COMPLETE_FAIL)


def verify_installation(deployment_id):
    logger.info("Verifying installation")

    exec_client = utils.get_cfy_client().executions
    executions = exec_client.list(deployment_id=deployment_id)
    check(len(executions) > 0, "No executions listed.")

    failed_executions = [e for e in executions if e.status == "failed"]
    check(len(failed_executions) == 0, "Execution failed.")

    install_execs = [e for e in executions if e.workflow_id == "install"]
    check(len(install_execs) == 1, "There is more than one install execution.")
    check(install_execs[0].status == "terminated",
          "Installation terminated in error.")

    outputs = get_outputs(deployment_id)
    check(len(outputs) > 0, "No outputs available")
    check("http_endpoint" in outputs, "No http endpoint present in outputs.")

    http_endpoint = outputs["http_endpoint"]
    m = re.match("https?://[^:]+(:[0-9]+)?", http_endpoint)
    check(m is not None, "Bad URL in outputs: {}.".format(http_endpoint))

    r = requests.get("{}/heartbeat/".format(http_endpoint))
    check(r.status_code == 200,
          "API not available. Got {} heartbeat.".format(r.status_code))

    r = requests.get(http_endpoint)
    check(r.status_code == 200,
          "GUI not available. Got {} on /.".format(r.status_code))


def update_state_file(file, deployment_id):
    logger.info("Writing test state file.")

    outputs = get_outputs(deployment_id)
    content = 'export TEST_DEPLOYMENT_SERVICE_ADDRESS="{}"\n'
    content = content.format(outputs["http_endpoint"])
    logger.debug("Content: {}".format(content))

    with open(file, "wb") as f:
        f.write(content)


def bootstrap(platform, test_state_file):
    deployment_id = os.path.basename(test_state_file)

    check_config()
    cfy_env = prepare_cfy_env()
    prepare_cfy_sandbox(cfy_env)
    execute_up(platform, deployment_id, cfy_env)
    wait_for_installation(deployment_id)
    verify_installation(deployment_id)

    update_state_file(test_state_file, deployment_id)

    sys.exit(EXIT_SUCCESS)


if __name__ == "__main__":
    bootstrap(*sys.argv[1:3])
