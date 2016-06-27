from unittest import TestCase
import os
import re
import subprocess
import time
import json
import requests

import utils
import settings

from cloudify_rest_client.exceptions import CloudifyClientError

class BootstrapTests(TestCase):
    """
    Test the procedure of bootstrapping (deploying) the DICE deployment tool.

    * Requires a running Cloudify Manager node to run.
    * An input file named inputs-$TARGET_PLATFORM.yaml should be in the parent
      directory.
    * Needs to be in a virtual environment with the proper version of the cfy
      CLI installed.
    """

    terminal_status = ['terminated', 'failed', 'cancelled']
    _cfy_client = None

    def non_terminal_executions(self, executions):
        return [e for e in executions if e.status not in self.terminal_status]

    def log(self, message):
        print message

    def undeploy(self):
        # initiate uninstall, but only if it hasn't been initiated before
        executions = self.cfy_client.executions.list(
            deployment_id=self.deployment_id)
        uninstalls = [e for e in executions if e.workflow_id == 'uninstall']
        if len(uninstalls) == 0 or uninstalls[0].status != 'terminated':
            self.log("Starting an uninstall workflow")
            execution = self.cfy_client.executions.start(
                deployment_id=self.deployment_id,
                workflow_id="uninstall")
            self.log("Uninstall execution %s" % execution.id)
            while not execution.status in self.terminal_status:
                time.sleep(5)
                execution = self.cfy_client.executions.get(
                    execution_id=execution.id)
            self.log("Finished uninstall execution")

        # try to delete the deployment
        deployment_exists = True
        try:
            self.cfy_client.deployments.get(self.deployment_id)
        except CloudifyClientError as e:
            deployment_exists = e.status_code != 404

        if deployment_exists:
            self.log("Deleting the deployment")
            attempts = 20
            while attempts > 0:
                try:
                    self.cfy_client.deployments.delete(self.deployment_id)
                    attempts = 0
                    deployment_exists = False
                except CloudifyClientError as e:
                    attempts -= 1
                    self.log("Failed deleting the deployment. %s "
                        "attempts to go. %s" % (attempts, e))
                    if attempts > 0:
                        time.sleep(5)

        if not deployment_exists:
            self.log("Deleting the blueprint")
            self.cfy_client.blueprints.delete(self.deployment_id)

    @property
    def cfy_client(self):
        if self._cfy_client is None:
            self._cfy_client = utils.get_cfy_client(settings)
        return self._cfy_client

    def get_outputs(self, deployment_id):
        outputs = self.cfy_client.deployments.outputs.get(
            deployment_id=deployment_id)
        return outputs["outputs"]

    def test_bootstrap(self):
        """
        Perform the bootstrap and verify if the application is responding.
        """

        # check that the inputs exist
        if not os.path.exists(settings.INPUTS_FILE_PATH):
            raise Exception("Inputs file not found in %s."
                            % settings.INPUTS_FILE_PATH)

        # pick a name for the deploy
        self.deployment_id = "it-dice-deployer-%s" % \
                str(time.time()).replace('.', '')

        # connect the cfy client to the Cloudify Manager
        if settings.CLOUDIFY_ADDRESS is None:
            raise Exception("Please define the CLOUDIFY_ADDRESS variable or setting")

        call_env = os.environ.copy()
        call_env['CLOUDIFY_USERNAME'] = settings.CLOUDIFY_USERNAME
        call_env['CLOUDIFY_PASSWORD'] = settings.CLOUDIFY_PASSWORD

        # initialize the cloudify client
        cfy_client = self.cfy_client

        # but we use the CLI tool to start the bootstrapping, because this
        # is what the users will use
        self.log("Connecting to the cloudify master at %s" % settings.CLOUDIFY_ADDRESS)
        proc = subprocess.Popen(["cfy", "use", "-t", settings.CLOUDIFY_ADDRESS],
            env=call_env, cwd=settings.BASE_DIR)
        retcode = proc.wait()
        self.assertEquals(0, retcode, "Failed to connect to the Cloudify "
            "manager. Check the CLOUDIFY_ADDRESS, CLOUDIFY_USERNAME and "
            "CLOUDIFY_PASSWORD settings values or environment parameters.")

        # run the ./up.sh
        self.log("Running ./up.sh {} {}".format(settings.TARGET_PLATFORM,
            self.deployment_id))
        proc = subprocess.Popen(["./up.sh", settings.TARGET_PLATFORM,
            self.deployment_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=call_env, cwd=os.path.dirname(settings.BASE_DIR))

        retcode = proc.poll()
        while retcode is None:
            self.log(proc.stdout.read())
            self.log(proc.stderr.read())

            time.sleep(2)
            retcode = proc.poll()

        self.log("Returned from up.sh")
        try:
            executions = cfy_client.executions.list(
                deployment_id=self.deployment_id)
            # at this point, the deploy:
            # * is ongoing (one of the executions is not terminated or failed)
            non_term_executions = self.non_terminal_executions(executions)
            if len(non_term_executions) > 0:
                self.log("Install not finished yet. Polling until it's done.")
                # we have already waited for 15 minutes. 10 minutes more should
                # be more than enough
                sleep_time = 5
                attempts = 120
                while len(non_term_executions) > 0 and attempts > 0:
                    time.sleep(sleep_time)
                    executions = cfy_client.executions.list(
                        deployment_id=self.deployment_id)
                    non_term_executions = self.non_terminal_executions(executions)
                    attempts -= 1

                if len(non_term_executions) > 0:
                    self.log("Installation takes too long. Cancelling.")
                    cfy_client.executions.cancel(
                        execution_id=non_term_executions[0].id)
                    # now wait a bit until it is really cancelled
                    attempts = 24
                    execution = cfy_client.executions.get(
                        execution_id=non_term_executions[0].id)
                    while execution.status != 'cancelled' and attempts > 0:
                        time.sleep(sleep_time)
                        attempts -= 1
                        execution = cfy_client.executions.get(
                            execution_id=execution.id)
                    if execution.status != 'cancelled':
                        raise Exception("The execution wouldn't cancel in due time.")
                    time.sleep(10) # TODO - find a way to wait for the end of the
                                  # hidden workflow _stop_deployment_environment
                    self.fail("Installation took too long.")

            # * has failed (no executions, or one of the executions has status
            #   failed)
            self.assertTrue(len(executions) > 0,
                "Failed before starting any executions")

            failed_executions = [e for e in executions if e.status == 'failed']
            if len(failed_executions) > 0:
                self.fail("Workflow %s failed" %
                    failed_executions[0].workflow_id)

            # * succeeded (all the executions are terminated, there is an
            #   install workflow)
            install_execs = [e for e in executions if e.workflow_id == 'install']
            self.assertEquals(1, len(install_execs))
            self.assertEquals('terminated', install_execs[0].status)

            # check the outputs
            outputs = self.get_outputs(deployment_id=self.deployment_id)
            self.assertNotEquals(0, len(outputs), "Outputs not available.")
            self.assertTrue("http_endpoint" in outputs)

            # is the output a valid URL?
            http_endpoint = outputs["http_endpoint"]
            m = re.match("https?://[^:]+:[0-9]+", http_endpoint)
            self.assertIsNotNone(m, "Bad URL in outputs: %s." % http_endpoint)

            # check if we can get to the API
            r = requests.get("%s/docs/" % http_endpoint)
            self.assertEquals(200, r.status_code,
                "API not available? Got HTTP %s on /docs/" % r.status_code)

            # check if we can get to the GUI
            r = requests.get("%s" % http_endpoint)
            self.assertEquals(200, r.status_code,
                "GUI not available? Got HTTP %s on /" % r.status_code)

        except Exception as e:
            self.log("Deployment failed: %s" % e)
            # dump the logs
            try:
                executions = cfy_client.executions.list(
                    deployment_id=self.deployment_id)
                for e in executions:
                    self.log("--------------------")
                    self.log("Workflow %s %s" % (e.workflow_id, e.status))
                    events = self.cfy_client.events.get(execution_id=e.id,
                        include_logs=True)
                    for event in events:
                        self.log(json.dumps(event, indent=4,
                            separators=(',', ': ')))

            except Exception as e:
                self.log("Getting the logs failed: %s" % str(e))
                pass

            self.fail(str(e))
        finally:
            self.log("Cleaning up")
            time.sleep(10)
            try:
                self.undeploy()
            except Exception as e:
                self.log("Failed undeploying: %s" % str(e))

