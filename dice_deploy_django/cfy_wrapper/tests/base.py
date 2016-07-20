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
        self.addCleanup(mock.patch.stopall)
