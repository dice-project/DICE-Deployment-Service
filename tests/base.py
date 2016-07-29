from unittest import TestCase

import requests
import settings
import utils
import uuid
import os


class BaseTest(TestCase):

    def setUp(self):
        assert settings.DEPLOYMENT_SERVICE_ADDRESS is not ""
        assert settings.DEPLOYMENT_SERVICE_USERNAME is not ""
        assert settings.DEPLOYMENT_SERVICE_PASSWORD is not ""

        self.cfy = utils.get_cfy_client()
        self.cleanup_queue = []

    def tearDown(self):
        # TODO process cleanup queue
        for b in self.cleanup_queue:
            print "Cleaning up {}".format(b)

    def add_blueprint_to_cleanup(self, blueprint):
        self.cleanup_queue.append(blueprint)

    @staticmethod
    def get_url(suffix):
        return "{}/{}".format(settings.DEPLOYMENT_SERVICE_ADDRESS, suffix)

    # Wrappers for requests that optionally add authentication
    @staticmethod
    def _request(method, suffix, auth, **kwargs):
        if auth:
            auth_url = BaseTest.get_url("auth/get-token")
            data = dict(username=settings.DEPLOYMENT_SERVICE_USERNAME,
                        password=settings.DEPLOYMENT_SERVICE_PASSWORD)
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
        blueprint = os.path.join(settings.BASE_DIR, "blueprints", name)
        assert os.path.isfile(blueprint)
        return blueprint

    @staticmethod
    def get_unique_str(prefix=None):
        suffix = str(uuid.uuid4())
        if prefix is None:
            return suffix
        return "{}-{}".format(prefix, suffix)
