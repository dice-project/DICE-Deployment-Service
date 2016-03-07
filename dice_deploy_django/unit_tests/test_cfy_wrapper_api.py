from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.conf import settings
from rest_framework.exceptions import NotFound
import os
from cfy_wrapper.models import Blueprint
import shutil
from django.core import management


class AccountTests(APITestCase):
    def setUp(self):
        # prevent data loss due to not setting settings_tests.py as settings module
        try:
            is_test_settings = settings.IS_TEST_SETTINGS
        except Exception, e:
            raise Exception(
                'Must run with dice_deploy/settings_tests.py. Aborting to prevent data loss.'
            )

        # clean uploads_tests folder prior starting
        if os.path.exists(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
        os.mkdir(settings.MEDIA_ROOT)

        # start celery
        management.call_command('celery-service', 'start', '--unit_tests')

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT)

        # stop celery
        # management.call_command('celery-service', 'stop', '--unit_tests')

    def test_upload_blueprint(self):
        """ Test uploading a new blueprint """
        url = reverse('blueprints')

        with open(os.path.join(settings.TEST_FILE_BLUEPRINT_EXAMPLE), 'rb') as f:
            # example = f.read()
            data = {'file': f}
            response = self.client.put(url, data)

        # check HTTP response
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED,
            msg='Recieved bad status: %d. Data was: %s' % (response.status_code, response.data)
        )
        self.assertDictContainsSubset({'state_name': 'pending'}, response.data)

        if 'cfy_id' not in response.data:
            raise AssertionError('Missing "cfy" key in response')

        # check DB state
        try:
            blueprint = Blueprint.get(response.data['cfy_id'])
        except NotFound:
            raise AssertionError('Blueprint was not found in DB, but it should be there.')

        # check filesystem
        with open(blueprint.archive.path) as f:
            data = f.read()
        if not data:
            raise AssertionError('Blueprint .tar.gz file could not be found/opened on filesystem')


