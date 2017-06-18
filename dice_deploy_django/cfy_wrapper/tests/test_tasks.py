from .base import BaseTest

from cfy_wrapper.models import Blueprint, Container, Input
from cfy_wrapper import tasks

from cloudify_rest_client.exceptions import CloudifyClientError

from django.test import override_settings

import mock


class BaseCeleryTest(BaseTest):

    def setUp(self):
        super(BaseCeleryTest, self).setUp()

        # No need to stop this patch, since parent's setUp function registered
        # cleanup for all mocks of this test case instance
        mock.patch.object(tasks, "logger").start()


@mock.patch("cfy_wrapper.tasks.upload_blueprint.client")
class UploadBlueprintTest(BaseCeleryTest):

    def test_valid_blueprint_upload(self, mock_cfy):
        b = Blueprint.objects.create()
        self.wd.write((str(b.id), "blueprint.yaml"), b"test: pair")
        c = Container.objects.create(blueprint=b)
        call = mock_cfy.blueprints.publish_archive

        tasks.upload_blueprint(c.cfy_id)

        b.refresh_from_db()
        call.assert_called_once_with(b.content_tar, b.cfy_id)

    def test_invalid_blueprint_upload(self, mock_cfy):
        b = Blueprint.objects.create()
        self.wd.write((str(b.id), "blueprint.yaml"), b"test: pair")
        c = Container.objects.create(blueprint=b)
        call = mock_cfy.blueprints.publish_archive
        call.side_effect = CloudifyClientError("test")

        with self.assertRaises(CloudifyClientError):
            tasks.upload_blueprint(c.cfy_id)


@mock.patch("cfy_wrapper.models.parser.parse_from_path")
@mock.patch("cfy_wrapper.tasks.create_deployment.client")
class CreateDeploymentTest(BaseCeleryTest):

    def test_valid(self, mock_cfy, mock_parse):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        c_call = mock_cfy.deployments.create
        l_call = mock_cfy.executions.list
        l_call.return_value = [mock.Mock(id="abc123")]
        mock_parse.return_value = {"inputs": {"1": "_1", "3": "_3"}}
        [Input.objects.create(key=str(i), value="v") for i in range(5)]

        result = tasks.create_deployment(c.cfy_id)

        b.refresh_from_db()
        c_call.assert_called_once_with(b.cfy_id, b.cfy_id,
                                       inputs={"1": "v", "3": "v"})
        l_call.assert_called_once_with(
            b.cfy_id, workflow_id="create_deployment_environment"
        )
        self.assertEqual(b.state, Blueprint.State.prepared_deployment)
        self.assertEqual("abc123", result)

    def test_invalid_input(self, mock_cfy, mock_parse):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        c_call = mock_cfy.deployments.create
        l_call = mock_cfy.executions.list
        mock_parse.return_value = {"inputs": {"1": "_1", "7": "_7"}}
        [Input.objects.create(key=str(i), value="v") for i in range(5)]

        with self.assertRaises(Blueprint.InputsError):
            tasks.create_deployment(c.cfy_id)

        c_call.assert_not_called()
        l_call.assert_not_called()

    def test_invalid(self, mock_cfy, mock_parse):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        c_call = mock_cfy.deployments.create
        c_call.side_effect = CloudifyClientError("test")
        l_call = mock_cfy.executions.list
        mock_parse.return_value = {"inputs": {"1": "_1", "3": "_3"}}
        [Input.objects.create(key=str(i), value="v") for i in range(5)]

        with self.assertRaises(CloudifyClientError):
            tasks.create_deployment(c.cfy_id)

        c_call.assert_called_once_with(b.cfy_id, b.cfy_id,
                                       inputs={"1": "v", "3": "v"})
        l_call.assert_not_called()


@override_settings(POOL_SLEEP_INTERVAL=0.01)
@mock.patch("cfy_wrapper.tasks.wait_for_execution.client")
class WaitForExecutionTest(BaseCeleryTest):

    def test_success(self, mock_cfy):
        l_call = mock_cfy.executions.get
        l_call.side_effect = [
            mock.Mock(status="started"), mock.Mock(status="terminated")
        ]

        tasks.wait_for_execution("e_id", False, "c_id")

        l_call.assert_has_calls([mock.call("e_id")] * 2)

    def test_success_immediate(self, mock_cfy):
        l_call = mock_cfy.executions.get

        tasks.wait_for_execution(None, False, "c_id")

        l_call.assert_not_called()

    def test_client_missing(self, mock_cfy):
        l_call = mock_cfy.executions.get
        l_call.side_effect = [
            mock.Mock(status="started"),
            CloudifyClientError("test", status_code=404)
        ]

        with self.assertRaises(CloudifyClientError):
            tasks.wait_for_execution("e_id", False, "c_id")

        l_call.assert_has_calls([mock.call("e_id")] * 2)

    def test_client_missing_ok(self, mock_cfy):
        l_call = mock_cfy.executions.get
        l_call.side_effect = [CloudifyClientError("test", status_code=404)]

        tasks.wait_for_execution("e_id", True, "c_id")

        l_call.assert_has_calls([mock.call("e_id")])

    def test_execution_failure(self, mock_cfy):
        l_call = mock_cfy.executions.get
        l_call.side_effect = [
            mock.Mock(status="started"), mock.Mock(status="failed")
        ]

        with self.assertRaises(Exception):
            tasks.wait_for_execution("e_id", False, "c_id")

        l_call.assert_has_calls([mock.call("e_id")] * 2)


@mock.patch("cfy_wrapper.tasks.install_blueprint.client")
class InstallTest(BaseCeleryTest):

    def test_success(self, mock_cfy):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        call = mock_cfy.executions.start
        call.return_value = mock.Mock(id="abc123")

        result = tasks.install_blueprint(c.cfy_id)

        call.assert_called_once_with(b.cfy_id, "install")
        self.assertEqual("abc123", result)

    def test_fail(self, mock_cfy):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        call = mock_cfy.executions.start
        call.side_effect = CloudifyClientError("test")

        with self.assertRaises(CloudifyClientError):
            tasks.install_blueprint(c.cfy_id)

        call.assert_called_once_with(b.cfy_id, "install")


@mock.patch("cfy_wrapper.tasks.fetch_blueprint_outputs.client")
class FetchOutputsTest(BaseCeleryTest):

    def test_success_non_empty(self, mock_cfy):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        deploys = mock_cfy.deployments
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
        deploys = mock_cfy.deployments
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
        deploys = mock_cfy.deployments
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
        deploys = mock_cfy.deployments
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


@mock.patch("cfy_wrapper.tasks.uninstall_blueprint.client")
class UninstallTest(BaseCeleryTest):

    def test_success(self, mock_cfy):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        call = mock_cfy.executions.start
        call.return_value = mock.Mock(id="abc123")

        result = tasks.uninstall_blueprint(c.cfy_id)

        call.assert_called_once_with(b.cfy_id, "uninstall")
        self.assertEqual("abc123", result)

    def test_fail(self, mock_cfy):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        call = mock_cfy.executions.start
        call.side_effect = CloudifyClientError("test")

        with self.assertRaises(CloudifyClientError):
            tasks.uninstall_blueprint(c.cfy_id)

        call.assert_called_once_with(b.cfy_id, "uninstall")


@mock.patch("cfy_wrapper.tasks.delete_deployment.client")
class DeleteDeploymentTest(BaseCeleryTest):

    def test_happy_path(self, mock_cfy):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        c_call = mock_cfy.deployments.delete
        l_call = mock_cfy.executions.list
        l_call.side_effect = CloudifyClientError("test", status_code=404)

        result = tasks.delete_deployment(c.cfy_id)

        b.refresh_from_db()
        c_call.assert_called_once_with(b.cfy_id)
        l_call.assert_called_once_with(
            b.cfy_id, workflow_id="delete_deployment_environment"
        )
        self.assertEqual(b.state, Blueprint.State.deleting_deployment)
        self.assertIsNone(result)

    def test_fail(self, mock_cfy):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        c_call = mock_cfy.deployments.delete
        c_call.side_effect = CloudifyClientError("test")
        l_call = mock_cfy.executions.list

        with self.assertRaises(CloudifyClientError):
            tasks.delete_deployment(c.cfy_id)

        c_call.assert_called_once_with(b.cfy_id)
        l_call.assert_not_called()

    def test_sad_path(self, mock_cfy):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        c_call = mock_cfy.deployments.delete
        l_call = mock_cfy.executions.list
        l_call.return_value = [mock.Mock(id="abc123")]

        result = tasks.delete_deployment(c.cfy_id)

        c_call.assert_called_once_with(b.cfy_id)
        l_call.assert_called_once_with(
            b.cfy_id, workflow_id="delete_deployment_environment"
        )
        self.assertEqual("abc123", result)


@mock.patch("cfy_wrapper.tasks.delete_blueprint.client")
class DeleteBlueprintTest(BaseCeleryTest):

    def test_valid(self, mock_cfy):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        call = mock_cfy.blueprints.delete

        tasks.delete_blueprint(c.cfy_id)

        b.refresh_from_db()
        call.assert_called_once_with(b.cfy_id)
        self.assertEqual(b.state, Blueprint.State.present)

    def test_invalid(self, mock_cfy):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        call = mock_cfy.blueprints.delete
        call.side_effect = CloudifyClientError("test")

        with self.assertRaises(CloudifyClientError):
            tasks.delete_blueprint(c.cfy_id)

        call.assert_called_once_with(b.cfy_id)


@mock.patch.object(tasks, "requests")
class RegisterAppTest(BaseCeleryTest):

    def test_all_ok(self, mock_requests):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        Input.objects.create(key="dmon_address", value="12.34.56.78:5001")
        mock_requests.put.return_value.status_code = 200

        tasks.register_app(c.cfy_id)

        b.refresh_from_db()
        self.assertEqual(0, b.errors.all().count())
        mock_requests.put.assert_called_once()

    def test_all_ok_metadata(self, mock_requests):
        b = Blueprint.objects.create()
        b.metadata.create(key="k 1", value="v 1")
        b.metadata.create(key="k 2", value="v 2")
        c = Container.objects.create(blueprint=b)
        Input.objects.create(key="dmon_address", value="12.34.56.78:5001")
        mock_requests.put.return_value.status_code = 200

        tasks.register_app(c.cfy_id)

        b.refresh_from_db()
        self.assertEqual(0, b.errors.all().count())
        mock_requests.put.assert_called_once()
        # This tests keyword arguments to put call
        self.assertEqual(mock_requests.put.mock_calls[0][2],
                         {"json": {"k 1": "v 1", "k 2": "v 2"}})

    def test_no_input(self, mock_requests):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)

        tasks.register_app(c.cfy_id)

        b.refresh_from_db()
        self.assertEqual(1, b.errors.all().count())
        e = b.errors.all()[0]
        self.assertTrue("Missing input" in e.message)
        mock_requests.put.assert_not_called()

    def test_bad_response(self, mock_requests):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        Input.objects.create(key="dmon_address", value="12.34.56.78:5001")
        mock_requests.put.return_value.status_code = 400

        tasks.register_app(c.cfy_id)

        b.refresh_from_db()
        self.assertEqual(1, b.errors.all().count())
        e = b.errors.all()[0]
        self.assertTrue("Application registration failed" in e.message)
        mock_requests.put.assert_called_once()


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


class GetDeployPipe(BaseCeleryTest):

    def test_nonempty_queue_no_register(self):
        b = Blueprint.objects.create()
        c = Container.objects.create(queue=b)

        pipe = tasks._get_deploy_pipe(c, False)

        self.assertEqual(6, len(pipe))

    def test_nonempty_queue_register(self):
        b = Blueprint.objects.create()
        c = Container.objects.create(queue=b)

        pipe = tasks._get_deploy_pipe(c, True)

        self.assertEqual(7, len(pipe))


# TODO: Add missing tests for sync_container
