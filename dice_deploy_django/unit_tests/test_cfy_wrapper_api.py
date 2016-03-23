from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.conf import settings
from rest_framework.exceptions import NotFound
import os
from cfy_wrapper.models import Blueprint, Container
import shutil
from django.core import management
import factories
from cfy_wrapper import serializers
from rest_framework.test import APIClient
from django.test import TransactionTestCase


class AccountTests(TransactionTestCase):
    """
    Extend TransactionTestCase instead of TestCase so that Celery worker can access the data.
    With TestCase, data would only exist in memory (as a transaction) and worker could not see it!
    """
    client_class = APIClient

    @classmethod
    def setUpClass(cls):
        super(AccountTests, cls).setUpClass()
        # prevent data loss due to not setting settings_tests.py as settings module
        try:
            is_test_settings = settings.IS_TEST_SETTINGS
        except Exception, e:
            raise Exception(
                'Must run with dice_deploy/settings_tests.py. Aborting to prevent data loss.'
            )

        # start celery test worker
        management.call_command('celery-service', 'start', '--unit_tests')

    @classmethod
    def tearDownClass(cls):
        super(AccountTests, cls).tearDownClass()
        # purge test queue
        management.call_command('celery-service', 'purge', '--unit_tests')

    def setUp(self):
        """ Is run before each test. """
        # clean uploads_tests folder prior starting
        if os.path.exists(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
        os.mkdir(settings.MEDIA_ROOT)

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT)

    def test_blueprint_list(self):
        url = reverse('blueprints')

        blue_pending = factories.BlueprintPendingFactory()
        blue_pending_ser = serializers.BlueprintSerializer(blue_pending).data

        blue_deployed = factories.BlueprintDeployedFactory()
        blue_deployed_ser = serializers.BlueprintSerializer(blue_deployed).data

        response = self.client.get(url)

        # check HTTP response
        self.assertEqual(
            response.status_code, status.HTTP_200_OK,
            msg='Recieved bad status: %d. Response was: %s' % (response.status_code, response.data)
        )

        self.assertListEqual([blue_pending_ser, blue_deployed_ser], response.data)

    def test_blueprint_details(self):
        blue_deployed = factories.BlueprintDeployedFactory()
        blue_deployed_ser = serializers.BlueprintSerializer(blue_deployed).data

        url = reverse('blueprint_id', kwargs={'blueprint_id': blue_deployed.id})

        response = self.client.get(url)

        # check HTTP response
        self.assertEqual(
            response.status_code, status.HTTP_200_OK,
            msg='Recieved bad status: %d. Response was: %s' % (response.status_code, response.data)
        )

        self.assertEqual(blue_deployed_ser, response.data)

    def test_blueprint_remove(self):
        blue_deployed = factories.BlueprintDeployedFactory()
        blue_deployed_ser = serializers.BlueprintSerializer(blue_deployed).data

        url = reverse('blueprint_id', kwargs={'blueprint_id': blue_deployed.id})

        response = self.client.delete(url)

        # check HTTP response
        self.assertEqual(
            response.status_code, status.HTTP_202_ACCEPTED,
            msg='Recieved bad status: %d. Response was: %s' % (response.status_code, response.data)
        )

    def test_container_create(self):
        url = reverse('containers')

        response = self.client.post(url)

        # check HTTP response
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED,
            msg='Recieved bad status: %d. Response was: %s' % (response.status_code, response.data)
        )
        self.assertDictContainsSubset({'blueprint': None}, response.data)

        if 'id' not in response.data:
            raise AssertionError('Missing "id" key in response')

        # check DB state
        try:
            container = Container.get(response.data['id'])
        except NotFound:
            raise AssertionError('Container was not found in DB, but it should be there.')

    def test_container_remove_empty(self):
        cont_empty = factories.ContainerEmptyFactory()

        url = reverse('container_id', kwargs={'container_id': cont_empty.id})
        response = self.client.delete(url)

        # check HTTP response
        self.assertEqual(
            response.status_code, status.HTTP_204_NO_CONTENT,
            msg='Recieved bad status: %d. Response was: %s' % (response.status_code, response.data)
        )

    def test_container_remove_full(self):
        cont_full = factories.ContainerFullFactory()

        url = reverse('container_id', kwargs={'container_id': cont_full.id})
        response = self.client.delete(url)

        # check HTTP response
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST,
            msg='Recieved bad status: %d. Response was: %s' % (response.status_code, response.data)
        )

    def test_container_list(self):
        url = reverse('containers')

        cont_empty = factories.ContainerEmptyFactory()
        cont_empty_ser = serializers.ContainerSerializer(cont_empty).data

        cont_full = factories.ContainerFullFactory()
        cont_full_ser = serializers.ContainerSerializer(cont_full).data

        response = self.client.get(url)

        # check HTTP response
        self.assertEqual(
            response.status_code, status.HTTP_200_OK,
            msg='Recieved bad status: %d. Response was: %s' % (response.status_code, response.data)
        )

        self.assertListEqual([cont_empty_ser, cont_full_ser], response.data)

    def test_container_details(self):
        cont_full = factories.ContainerFullFactory()
        cont_full_ser = serializers.ContainerSerializer(cont_full).data

        url = reverse('container_id', kwargs={'container_id': cont_full.id})
        response = self.client.get(url)

        # check HTTP response
        self.assertEqual(
            response.status_code, status.HTTP_200_OK,
            msg='Recieved bad status: %d. Response was: %s' % (response.status_code, response.data)
        )

        self.assertEqual(cont_full_ser, response.data)

    def test_container_details_non_existent(self):
        cont_full = factories.ContainerFullFactory.build()  # unsaved

        url = reverse('container_id', kwargs={'container_id': cont_full.id})
        response = self.client.get(url)

        # check HTTP response
        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND,
            msg='Recieved bad status: %d. Response was: %s' % (response.status_code, response.data)
        )

    def test_container_blueprint_upload_to_empty(self):
        cont_empty = factories.ContainerEmptyFactory()
        url = reverse('container_blueprint', kwargs={'container_id': cont_empty.id})

        with open(os.path.join(settings.TEST_FILE_BLUEPRINT_EXAMPLE), 'rb') as f:
            data = {'file': f}
            response = self.client.post(url, data)

        # check HTTP response
        self.assertEqual(
            response.status_code, status.HTTP_202_ACCEPTED,
            msg='Recieved bad status: %d. Response was: %s' % (response.status_code, response.data)
        )

        # check DB state
        try:
            cont = Container.get(response.data['id'])
            blueprint = Blueprint.get(response.data['blueprint']['cfy_id'])
        except NotFound:
            raise AssertionError('Container or Blueprint was not found in DB, but it should be there.')

        self.assertEqual(cont.blueprint, blueprint)

        # check filesystem
        with open(blueprint.archive.path) as f:
            data = f.read()
        if not data:
            raise AssertionError('Blueprint .tar.gz file could not be found/opened on filesystem')

    def test_container_blueprint_upload_to_full(self):
        cont_full = factories.ContainerFullFactory()
        url = reverse('container_blueprint', kwargs={'container_id': cont_full.id})

        with open(os.path.join(settings.TEST_FILE_BLUEPRINT_EXAMPLE), 'rb') as f:
            data = {'file': f}
            response = self.client.post(url, data)

        # check HTTP response
        self.assertEqual(
            response.status_code, status.HTTP_202_ACCEPTED,
            msg='Recieved bad status: %d. Response was: %s' % (response.status_code, response.data)
        )

        # check DB state
        try:
            cont = Container.get(response.data['id'])
            blueprint = Blueprint.get(response.data['blueprint']['cfy_id'])
        except NotFound:
            raise AssertionError('Container or Blueprint was not found in DB, but it should be there.')

        self.assertEqual(cont.blueprint, blueprint)

        # check filesystem
        with open(blueprint.archive.path) as f:
            data = f.read()
        if not data:
            raise AssertionError('Blueprint .tar.gz file could not be found/opened on filesystem')

    def test_container_blueprint_redeploy_empty(self):
        cont_empty = factories.ContainerEmptyFactory()
        url = reverse('container_blueprint', kwargs={'container_id': cont_empty.id})

        response = self.client.put(url)

        # check HTTP response
        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND,
            msg='Recieved bad status: %d. Response was: %s' % (response.status_code, response.data)
        )

    def test_container_blueprint_redeploy_full(self):
        cont_full = factories.ContainerFullFactory()
        url = reverse('container_blueprint', kwargs={'container_id': cont_full.id})

        response = self.client.put(url)

        # check HTTP response
        self.assertEqual(
            response.status_code, status.HTTP_202_ACCEPTED,
            msg='Recieved bad status: %d. Response was: %s' % (response.status_code, response.data)
        )

    def test_delete_blueprint_but_not_container(self):
        cont_full = factories.ContainerFullFactory()
        blueprint = cont_full.blueprint
        blueprint.delete()

        cont_full.refresh_from_db()
        self.assertNotEqual(None, cont_full)

