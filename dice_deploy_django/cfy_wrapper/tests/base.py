from django.contrib.auth.models import User
from django.conf import settings
from rest_framework.authtoken.models import Token
from rest_framework.test import (
    APITestCase,
    APIRequestFactory,
    force_authenticate
)
from testfixtures import TempDirectory

from collections import namedtuple
import mock

# IMPORTANT!!!
#
# Any test that creates blueprint should be derived from BaseTest that will
# properly override MEDIA_ROOT configuration setting. There are three benefits
# of doing this:
#
#   - BaseTest will make sure MEDIA_ROOT is set to some temporary folder,
#     which will prevent most incidents of running tests on production setup
#     and messing up user data,
#   - each test is run in separate folder, which makes is easier to track the
#     contents of the folder
#   - tests can be run in parallel, since each test works in separate folder
#
# Take these instructions as a friendly advice and follow them always.


class BaseTest(APITestCase):
    """
    Base test case

    Main purpose of this base case is to provide per-test-case MEDIA_ROOT
    temporary directory that can be used for safely running tests in
    isolation.
    """

    def setUp(self):
        self.wd = TempDirectory()
        self.addCleanup(self.wd.cleanup)

        # Django settings patches
        mock.patch.object(settings, "MEDIA_ROOT", self.wd.path).start()
        mock.patch.object(settings, "CELERY_ALWAYS_EAGER", True).start()
        self.addCleanup(mock.patch.stopall)


Field = namedtuple("Field", ["source", "conv", "target"])


class BaseViewTest(BaseTest):
    """
    Extended base test

    This test case also has various clients and authentication details
    pregenerated.
    """

    def setUp(self):
        super(BaseViewTest, self).setUp()
        self.rfactory = APIRequestFactory()
        User.objects.create_superuser(username="test", password="pass",
                                      email="test@example.com")
        self.token = Token.objects.first()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def _gen_request(self, url, method, auth, data, format):
        req = getattr(self.rfactory, method)(url, data=data, format=format)
        if auth:
            force_authenticate(req, user=self.token.user, token=self.token)
        return req

    def get(self, url, auth):
        return self._gen_request(url, "get", auth, None, "json")

    def post(self, url, data, auth, format="json"):
        return self._gen_request(url, "post", auth, data, format)

    def put(self, url, data, auth, format="json"):
        return self._gen_request(url, "put", auth, data, format)

    def delete(self, url, auth):
        return self._gen_request(url, "delete", auth, None, "json")

    def compare(self, fields, data, truth):
        id = fields[0]
        fields = fields[1:]

        data = data if isinstance(data, list) else [data]
        truth = truth if isinstance(truth, list) else [truth]

        data = array2dict(data, id.target)
        self.assertEqual(len(data), len(truth))
        for t in truth:
            d = data[id.conv(getattr(t, id.source))]
            for source, conv, target in fields:
                self.assertEqual(d[target], conv(getattr(t, source)))


def array2dict(arr, key):
    return {v[key]: v for v in arr}


def date2str(date):
    return date.strftime(settings.API_DT_FORMAT)


def identity(x):
    return x
