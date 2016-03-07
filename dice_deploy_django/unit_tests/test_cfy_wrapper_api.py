from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from dice_deploy import settings_tests
import os


class AccountTests(APITestCase):
    def test_upload_blueprint(self):
        """ Test uploading a new blueprint """
        url = reverse('blueprints')

        example = None
        with open(os.path.join(settings_tests.TEST_FILES_DIR, 'example.tar.gz'), 'rb') as f:
            example = f.read()

        data = {'file': example}
        response = self.client.put(url, data)

        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED,
            msg='Recieved bad status: %d. Data was: %s' % (response.status_code, response.data)
        )
        self.assertDictContainsSubset({'state_name': 'pending'}, response.data)

        if 'cfy_id' not in response.data:
            raise AssertionError('Missing "cfy" key in response')
