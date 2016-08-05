from .base import BaseTest

from cfy_wrapper.models import Blueprint, Container
from cfy_wrapper import tasks

from cloudify_rest_client.exceptions import CloudifyClientError

from django.test import override_settings

import mock


class UpdateStateTest(BaseTest):

    def test_default(self):
        b = Blueprint.objects.create()
        state = Blueprint.State.installed
        tasks._update_state(b.cfy_id, state)

        b.refresh_from_db()
        self.assertEqual(b.state, state)

    def test_success(self):
        b = Blueprint.objects.create()
        state = Blueprint.State.installed
        tasks._update_state(b.cfy_id, state, True)

        b.refresh_from_db()
        self.assertEqual(b.state, state)

    def test_fail(self):
        b = Blueprint.objects.create()
        state = Blueprint.State.installed
        tasks._update_state(b.cfy_id, state, False)

        b.refresh_from_db()
        self.assertEqual(b.state, -state)


@override_settings(POOL_SLEEP_INTERVAL=0.01)
class WaitForExecutionTest(BaseTest):

    def test_success(self):
        execution = mock.Mock(status="started")
        client = mock.Mock()
        client.executions.get.side_effect = [
            mock.Mock(status="started"), mock.Mock(status="terminated")
        ]

        self.assertTrue(tasks._wait_for_execution(client, execution))

    def test_success_immediate(self):
        execution = mock.Mock(status="terminated")
        client = mock.Mock()

        self.assertTrue(tasks._wait_for_execution(client, execution))
        client.executions.get.assert_not_called()

    def test_client_failure(self):
        execution = mock.Mock(status="started")
        client = mock.Mock()
        client.executions.get.side_effect = CloudifyClientError("test")

        self.assertFalse(tasks._wait_for_execution(client, execution))

    def test_client_failure_force_success(self):
        execution = mock.Mock(status="started")
        client = mock.Mock()
        client.executions.get.side_effect = CloudifyClientError(
            "test", status_code=404
        )

        self.assertTrue(tasks._wait_for_execution(client, execution, True))

    def test_execution_failure(self):
        execution = mock.Mock(status="started")
        client = mock.Mock()
        client.executions.get.side_effect = [
            mock.Mock(status="started"), mock.Mock(status="failed")
        ]

        self.assertFalse(tasks._wait_for_execution(client, execution))


@mock.patch("cfy_wrapper.utils.CloudifyClient")
@mock.patch.object(tasks, "_wait_for_execution")
@mock.patch.object(tasks, "_update_state")
@mock.patch.object(tasks, "_cancel_chain_execution")
class RunWorkflowTest(BaseTest):

    def test_start_fail(self, mock_cancel, mock_update, mock_wait, mock_cfy):
        task = mock.Mock()
        mock_cfy.return_value.executions.start.side_effect = \
            CloudifyClientError("test")

        res = tasks._run_workflow(task, "w", "c", "b", 1, 2)

        self.assertFalse(res)
        mock_update.assert_has_calls([mock.call("b", 1),
                                      mock.call("b", 1, False)])
        mock_cancel.assert_called_once_with(task, "c")
        mock_wait.assert_not_called()

    def test_wait_fail(self, mock_cancel, mock_update, mock_wait, mock_cfy):
        task = mock.Mock()
        execution = mock.Mock(status="pending")
        mock_cfy.return_value.executions.start.return_value = execution
        mock_wait.return_value = False

        res = tasks._run_workflow(task, "w", "c", "b", 1, 2)

        self.assertFalse(res)
        mock_update.assert_has_calls([mock.call("b", 1),
                                      mock.call("b", 2, False)])
        mock_cancel.assert_called_once_with(task, "c")
        mock_wait.assert_called_once_with(mock_cfy.return_value, execution)

    def test_success(self, mock_cancel, mock_update, mock_wait, mock_cfy):
        task = mock.Mock()
        execution = mock.Mock(status="started")
        mock_cfy.return_value.executions.start.return_value = execution
        mock_wait.return_value = True

        res = tasks._run_workflow(task, "w", "c", "b", 1, 2)

        self.assertTrue(res)
        mock_update.assert_has_calls([mock.call("b", 1),
                                      mock.call("b", 2, True)])
        mock_cancel.assert_not_called()
        mock_wait.assert_called_once_with(mock_cfy.return_value, execution)


class BaseCeleryTest(BaseTest):

    def setUp(self):
        super(BaseCeleryTest, self).setUp()

        # No need to stop this patch, since parent's setUp function registered
        # cleanup for all mocks of this test case instance
        mock.patch.object(tasks, "logger").start()


@mock.patch.object(tasks, "_cancel_chain_execution")
@mock.patch("cfy_wrapper.utils.CloudifyClient")
class UploadBlueprintTest(BaseCeleryTest):

    def test_valid_blueprint_upload(self, mock_cfy, mock_cancel):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        call = mock_cfy.return_value.blueprints.publish_archive

        tasks.upload_blueprint(c.cfy_id)

        b.refresh_from_db()
        call.assert_called_once_with(b.content_tar, b.cfy_id)
        mock_cancel.assert_not_called()
        self.assertEqual(b.state, Blueprint.State.uploaded_to_cloudify)

    def test_invalid_blueprint_upload(self, mock_cfy, mock_cancel):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        call = mock_cfy.return_value.blueprints.publish_archive
        call.side_effect = CloudifyClientError("test")

        tasks.upload_blueprint(c.cfy_id)

        b.refresh_from_db()
        call.assert_called_once_with(b.content_tar, b.cfy_id)
        mock_cancel.assert_called_once()
        self.assertEqual(c.cfy_id, mock_cancel.mock_calls[0][1][1])
        self.assertEqual(b.state, -Blueprint.State.uploading_to_cloudify)


@mock.patch.object(tasks, "_cancel_chain_execution")
@mock.patch.object(tasks, "_wait_for_execution")
@mock.patch("cfy_wrapper.utils.CloudifyClient")
class CreateDeploymentTest(BaseCeleryTest):

    def test_valid(self, mock_cfy, mock_wait, mock_cancel):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        c_call = mock_cfy.return_value.deployments.create
        l_call = mock_cfy.return_value.executions.list
        l_call.return_value = \
            [mock.Mock(workflow_id="create_deployment_environment")]
        mock_wait.return_value = True

        tasks.create_deployment(c.cfy_id)

        b.refresh_from_db()
        c_call.assert_called_once_with(b.cfy_id, b.cfy_id)
        l_call.assert_called_once_with(b.cfy_id)
        mock_wait.assert_called_once()
        mock_cancel.assert_not_called()
        self.assertEqual(b.state, Blueprint.State.prepared_deployment)

    def test_invalid(self, mock_cfy, mock_wait, mock_cancel):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        c_call = mock_cfy.return_value.deployments.create
        c_call.side_effect = CloudifyClientError("test")

        tasks.create_deployment(c.cfy_id)

        b.refresh_from_db()
        c_call.assert_called_once_with(b.cfy_id, b.cfy_id)
        mock_wait.assert_not_called()
        mock_cancel.assert_called_once()
        self.assertEqual(c.cfy_id, mock_cancel.mock_calls[0][1][1])
        self.assertEqual(b.state, -Blueprint.State.preparing_deployment)

    def test_invalid_wait(self, mock_cfy, mock_wait, mock_cancel):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        c_call = mock_cfy.return_value.deployments.create
        l_call = mock_cfy.return_value.executions.list
        l_call.return_value = \
            [mock.Mock(workflow_id="create_deployment_environment")]
        mock_wait.return_value = False

        tasks.create_deployment(c.cfy_id)

        b.refresh_from_db()
        c_call.assert_called_once_with(b.cfy_id, b.cfy_id)
        l_call.assert_called_once_with(b.cfy_id)
        mock_wait.assert_called_once()
        mock_cancel.assert_called_once()
        self.assertEqual(c.cfy_id, mock_cancel.mock_calls[0][1][1])
        self.assertEqual(b.state, -Blueprint.State.prepared_deployment)


@mock.patch.object(tasks, "_run_workflow")
class InstallTest(BaseCeleryTest):

    def test_success(self, mock_run):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        mock_run.return_value = True
        tasks.install_blueprint(c.cfy_id)

        mock_run.assert_called_once()
        # Next line: get all but first positional param of first mock call
        call_params_without_task = mock_run.mock_calls[0][1][1:]
        self.assertEqual(call_params_without_task,
                         ("install", c.cfy_id, b.cfy_id,
                          Blueprint.State.installing,
                          Blueprint.State.installed))

    def test_fail(self, mock_run):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        mock_run.return_value = False
        tasks.install_blueprint(c.cfy_id)

        mock_run.assert_called_once()
        # Next line: get all but first positional param of first mock call
        call_params_without_task = mock_run.mock_calls[0][1][1:]
        self.assertEqual(call_params_without_task,
                         ("install", c.cfy_id, b.cfy_id,
                          Blueprint.State.installing,
                          Blueprint.State.installed))


@mock.patch("cfy_wrapper.utils.CloudifyClient")
class FetchOutputsTest(BaseCeleryTest):

    def test_success_non_empty(self, mock_cfy):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        deploys = mock_cfy.return_value.deployments
        deploys.get.return_value = {
            "key": "value",
            "outputs": {
                "sample-output": {
                    "description": "sample-desc",
                    "value": "some-value",
                }
            }
        }
        deploys.outputs.get.return_value = {
            "key": "value",
            "outputs": {
                "sample-output": "another-value",
            }
        }
        result = {
            "sample-output": {
                "description": "sample-desc",
                "value": "another-value",
            }
        }

        tasks.fetch_blueprint_outputs(c.cfy_id)

        b.refresh_from_db()
        self.assertEqual(b.outputs, result)
        self.assertEqual(b.state, Blueprint.State.deployed)

    def test_success_empty(self, mock_cfy):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        deploys = mock_cfy.return_value.deployments
        deploys.get.return_value = {
            "key": "value",
            "outputs": {
                "sample-output": {
                    "description": "sample-desc",
                    "value": "some-value",
                }
            }
        }
        deploys.outputs.get.return_value = {}
        result = {}

        tasks.fetch_blueprint_outputs(c.cfy_id)

        b.refresh_from_db()
        self.assertEqual(b.outputs, result)
        self.assertEqual(b.state, Blueprint.State.deployed)

    def test_success_missing_desc(self, mock_cfy):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        deploys = mock_cfy.return_value.deployments
        deploys.get.return_value = {
            "key": "value",
            "outputs": {
                "sample-output": {
                    "value": "some-value",
                }
            }
        }
        deploys.outputs.get.return_value = {
            "key": "value",
            "outputs": {
                "sample-output": "another-value",
            }
        }
        result = {
            "sample-output": {
                "description": "",
                "value": "another-value",
            }
        }

        tasks.fetch_blueprint_outputs(c.cfy_id)

        b.refresh_from_db()
        self.assertEqual(b.outputs, result)
        self.assertEqual(b.state, Blueprint.State.deployed)

    def test_success_empty_desc(self, mock_cfy):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        deploys = mock_cfy.return_value.deployments
        deploys.get.return_value = {"key": "value"}
        deploys.outputs.get.return_value = {
            "key": "value",
            "outputs": {
                "sample-output": "another-value",
            }
        }
        result = {
            "sample-output": {
                "description": "",
                "value": "another-value",
            }
        }

        tasks.fetch_blueprint_outputs(c.cfy_id)

        b.refresh_from_db()
        self.assertEqual(b.outputs, result)
        self.assertEqual(b.state, Blueprint.State.deployed)


@mock.patch.object(tasks, "_run_workflow")
class UninstallTest(BaseCeleryTest):

    def test_success(self, mock_run):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        mock_run.return_value = True

        tasks.uninstall_blueprint(c.cfy_id)

        mock_run.assert_called_once()
        # Next line: get all but first positional param of first mock call
        call_params_without_task = mock_run.mock_calls[0][1][1:]
        self.assertEqual(call_params_without_task,
                         ("uninstall", c.cfy_id, b.cfy_id,
                          Blueprint.State.uninstalling,
                          Blueprint.State.uninstalled))

    def test_fail(self, mock_run):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        mock_run.return_value = False

        tasks.uninstall_blueprint(c.cfy_id)

        mock_run.assert_called_once()
        # Next line: get all but first positional param of first mock call
        call_params_without_task = mock_run.mock_calls[0][1][1:]
        self.assertEqual(call_params_without_task,
                         ("uninstall", c.cfy_id, b.cfy_id,
                          Blueprint.State.uninstalling,
                          Blueprint.State.uninstalled))


@mock.patch.object(tasks, "_cancel_chain_execution")
@mock.patch.object(tasks, "_wait_for_execution")
@mock.patch("cfy_wrapper.utils.CloudifyClient")
class DeleteDeploymentTest(BaseCeleryTest):

    def test_happy_path(self, mock_cfy, mock_wait, mock_cancel):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        c_call = mock_cfy.return_value.deployments.delete
        l_call = mock_cfy.return_value.executions.list
        l_call.side_effect = CloudifyClientError("test", status_code=404)

        tasks.delete_deployment(c.cfy_id)

        b.refresh_from_db()
        c_call.assert_called_once_with(b.cfy_id)
        l_call.assert_called_once_with(b.cfy_id)
        mock_wait.assert_not_called()
        mock_cancel.assert_not_called()
        self.assertEqual(b.state, Blueprint.State.deleted_deployment)

    def test_fail(self, mock_cfy, mock_wait, mock_cancel):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        c_call = mock_cfy.return_value.deployments.delete
        c_call.side_effect = CloudifyClientError("test")
        l_call = mock_cfy.return_value.executions.list

        tasks.delete_deployment(c.cfy_id)

        b.refresh_from_db()
        c_call.assert_called_once_with(b.cfy_id)
        l_call.assert_not_called()
        mock_wait.assert_not_called()
        mock_cancel.assert_called_once()
        self.assertEqual(c.cfy_id, mock_cancel.mock_calls[0][1][1])
        self.assertEqual(b.state, -Blueprint.State.deleting_deployment)

    def test_sad_path_success(self, mock_cfy, mock_wait, mock_cancel):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        c_call = mock_cfy.return_value.deployments.delete
        l_call = mock_cfy.return_value.executions.list
        l_call.return_value = \
            [mock.Mock(workflow_id="delete_deployment_environment")]
        mock_wait.return_value = True

        tasks.delete_deployment(c.cfy_id)

        b.refresh_from_db()
        c_call.assert_called_once_with(b.cfy_id)
        l_call.assert_called_once_with(b.cfy_id)
        mock_wait.assert_called_once()
        mock_cancel.assert_not_called()
        self.assertEqual(b.state, Blueprint.State.deleted_deployment)

    def test_sad_path_fail(self, mock_cfy, mock_wait, mock_cancel):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        c_call = mock_cfy.return_value.deployments.delete
        l_call = mock_cfy.return_value.executions.list
        l_call.return_value = \
            [mock.Mock(workflow_id="delete_deployment_environment")]
        mock_wait.return_value = False

        tasks.delete_deployment(c.cfy_id)

        b.refresh_from_db()
        c_call.assert_called_once_with(b.cfy_id)
        l_call.assert_called_once_with(b.cfy_id)
        mock_wait.assert_called_once()
        mock_cancel.assert_called_once()
        self.assertEqual(c.cfy_id, mock_cancel.mock_calls[0][1][1])
        self.assertEqual(b.state, -Blueprint.State.deleted_deployment)


@mock.patch.object(tasks, "_cancel_chain_execution")
@mock.patch("cfy_wrapper.utils.CloudifyClient")
class DeleteBlueprintTest(BaseCeleryTest):

    def test_valid(self, mock_cfy, mock_cancel):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        call = mock_cfy.return_value.blueprints.delete

        tasks.delete_blueprint(c.cfy_id)

        b.refresh_from_db()
        call.assert_called_once_with(b.cfy_id)
        mock_cancel.assert_not_called()
        self.assertEqual(b.state, Blueprint.State.present)

    def test_invalid(self, mock_cfy, mock_cancel):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        call = mock_cfy.return_value.blueprints.delete
        call.side_effect = CloudifyClientError("test")

        tasks.delete_blueprint(c.cfy_id)

        b.refresh_from_db()
        call.assert_called_once_with(b.cfy_id)
        mock_cancel.assert_called_once()
        self.assertEqual(c.cfy_id, mock_cancel.mock_calls[0][1][1])
        self.assertEqual(c.cfy_id, mock_cancel.mock_calls[0][1][1])
        self.assertEqual(b.state, -Blueprint.State.deleting_from_cloudify)


class ProcessContainerQueue(BaseCeleryTest):

    def test_deploy(self):
        b = Blueprint.objects.create()
        c = Container.objects.create(queue=b)

        tasks.process_container_queue(c.cfy_id)

        c.refresh_from_db()
        self.assertEqual(c.blueprint, b)
        self.assertIsNone(c.queue)

    def test_undeploy(self):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)

        tasks.process_container_queue(c.cfy_id)

        c.refresh_from_db()
        self.assertIsNone(c.blueprint)
        self.assertIsNone(c.queue)
        self.assertEqual(0, Blueprint.objects.all().count())

    def test_undeploy_deploy(self):
        b1 = Blueprint.objects.create()
        b2 = Blueprint.objects.create()
        c = Container.objects.create(queue=b2, blueprint=b1)

        tasks.process_container_queue(c.cfy_id)

        c.refresh_from_db()
        b2 = Blueprint.objects.get(id=b2.id)
        self.assertEqual(c.blueprint, b2)
        self.assertIsNone(c.queue)
        self.assertEqual(0, Blueprint.objects.filter(id=b1.id).count())

    def test_redeploy(self):
        b = Blueprint.objects.create()
        c = Container.objects.create(queue=b, blueprint=b)

        tasks.process_container_queue(c.cfy_id)

        c.refresh_from_db()
        b = Blueprint.objects.get(id=b.id)
        self.assertEqual(c.blueprint, b)
        self.assertIsNone(c.queue)


# TODO: Add missing tests for sync_container and pipe helpers
