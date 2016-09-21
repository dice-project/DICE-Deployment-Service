from unittest import TestCase

import requests
import utils
import time
import uuid
import os


class TimeoutException(Exception):
    pass


class BaseTest(TestCase):

    def setUp(self):
        assert os.environ["TEST_DEPLOYMENT_SERVICE_ADDRESS"] is not ""
        assert os.environ["TEST_SUPERUSER_USERNAME"] is not ""
        assert os.environ["TEST_SUPERUSER_PASSWORD"] is not ""
        wait_time = int(os.environ.get("TEST_WAIT_TIME", 30)) * 60

        self.cfy = utils.get_cfy_client()
        self.cleanup_queue = []
        self.end_time = time.time() + wait_time

    def tearDown(self):
        # TODO process cleanup queue
        for b in self.cleanup_queue:
            print "Cleaning up {}".format(b)

    def run(self, result=None):
        # Stop test execution if we encountered error.
        super(BaseTest, self).run(result)
        if result.errors:
            result.stop()

    def add_blueprint_to_cleanup(self, blueprint):
        self.cleanup_queue.append(blueprint)

    def fail_on_timeout(self):
        if self.end_time < time.time():
            # We do not fail here because timeout indicates that either test
            # runner is misconfigured or platform that tests are being run
            # against is having troubles. Continuing to run in under such
            # conditions makes little sense, so we error out here to abort any
            # pending tests.
            raise TimeoutException()
        return True

    @staticmethod
    def get_url(suffix):
        return "{}/{}".format(os.environ["TEST_DEPLOYMENT_SERVICE_ADDRESS"],
                              suffix)

    # Wrappers for requests that optionally add authentication
    @staticmethod
    def _request(method, suffix, auth, **kwargs):
        if auth:
            auth_url = BaseTest.get_url("auth/get-token")
            data = dict(username=os.environ["TEST_SUPERUSER_USERNAME"],
                        password=os.environ["TEST_SUPERUSER_PASSWORD"])
            token = requests.post(auth_url, json=data).json()["token"]
            kwargs["headers"] = {
                "Authorization": "Token {}".format(token),
            }
        return method(BaseTest.get_url(suffix), **kwargs)

    @staticmethod
    def get(suffix, auth):
        return BaseTest._request(requests.get, suffix, auth)

    @staticmethod
    def post(suffix, auth, **kwargs):
        return BaseTest._request(requests.post, suffix, auth, **kwargs)

    @staticmethod
    def delete(suffix, auth):
        return BaseTest._request(requests.delete, suffix, auth)

    # Helpers for retrieving test data, generating (almost) unique names, etc.
    @staticmethod
    def get_blueprint(name):
        blueprint = os.path.join(utils.BASE_DIR, "blueprints", name)
        assert os.path.isfile(blueprint)
        return blueprint

    @staticmethod
    def get_unique_str(prefix=None):
        suffix = str(uuid.uuid4())
        if prefix is None:
            return suffix
        return "{}-{}".format(prefix, suffix)
