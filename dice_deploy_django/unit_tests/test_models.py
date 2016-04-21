from django.core.urlresolvers import reverse
from rest_framework import status
from django.conf import settings
from rest_framework.exceptions import NotFound
import os
from cfy_wrapper.models import Blueprint, Container, Input
import shutil
from django.core import management
import factories
from cfy_wrapper import serializers
from rest_framework.test import APIClient
from django.test import TestCase
import tarfile
import yaml as yaml_lib


class ModelsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super(ModelsTests, cls).setUpClass()
        # prevent data loss due to not setting settings_tests.py as settings module
        try:
            is_test_settings = settings.IS_TEST_SETTINGS
        except Exception, e:
            raise Exception(
                'Must run with dice_deploy/settings_tests.py. Aborting to prevent data loss.'
            )

    def setUp(self):
        """ Is run before each test. """
        # clean uploads_tests folder prior starting
        if os.path.exists(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
        os.mkdir(settings.MEDIA_ROOT)

        # clean tmp folder prior starting
        if os.path.exists(settings.TEST_FILES_TMP_DIR):
            shutil.rmtree(settings.TEST_FILES_TMP_DIR)
        os.mkdir(settings.TEST_FILES_TMP_DIR)

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        shutil.rmtree(settings.TEST_FILES_TMP_DIR, ignore_errors=True)

    def test_delete_blueprint_but_not_container(self):
        cont_full = factories.ContainerFullGzipFactory()
        blueprint = cont_full.blueprint
        blueprint.delete()

        cont_full.refresh_from_db()
        self.assertNotEqual(None, cont_full)

    def test_generate_gzip_file(self):
        blueprint = factories.BlueprintYamlDeployedFactory()

        archive_filename = blueprint.generate_archive()

        # check that created archive file has some size
        self.assertTrue(os.path.getsize(archive_filename) > 0, 'Archive size should not be zero')

        # check that created archive exists and is a valid .tar.gz
        try:
            with tarfile.open(archive_filename, 'r:gz') as tar:
                self.assertIsNotNone(tar)
        except tarfile.TarError, e:
            raise AssertionError('Expected a valid .tar.gz archive, but got error: %s' % e)

    def test_generate_multiple_gzip_files(self):
        blueprint1 = factories.BlueprintYamlDeployedFactory()
        archive_filename1 = blueprint1.generate_archive()

        blueprint2 = factories.BlueprintYamlDeployedFactory()
        archive_filename2 = blueprint2.generate_archive()

        # check that created archive files have some size
        self.assertTrue(os.path.getsize(archive_filename1) > 0, 'Archive size should not be zero')
        self.assertTrue(os.path.getsize(archive_filename2) > 0, 'Archive size should not be zero')


    def test_append_inputs_into_yaml(self):
        TMP_FOLDER = os.path.join(settings.TEST_FILES_TMP_DIR, 'check_yaml_inputs')

        input1 = factories.InputFactory.create(key='key1', value='val1', description='Description1')
        input2 = factories.InputFactory.create(key='key2', value='val2', description='Description2')
        input3 = factories.InputFactory.create(key='key3', value='val3', description='Description3')
        inputs = [input1, input2, input3]

        blueprint = factories.BlueprintYamlDeployedFactory()
        archive_filename = blueprint.generate_archive()

        # extract archive
        with tarfile.open(archive_filename, mode='r:gz') as tar:
            tar.extractall(path=TMP_FOLDER)

        # check content in yaml
        with open(os.path.join(TMP_FOLDER, settings.ARCHIVE_FOLDER_NAME, settings.YAML_NAME), 'r') as f:
            yaml_obj = yaml_lib.load(f)
            if 'inputs' not in yaml_obj:
                raise AssertionError('"intputs" are not in yaml, but should be')
            for el in inputs:
                if el.key not in yaml_obj['inputs'] or \
                                yaml_obj['inputs'][el.key]['description'] != el.description:
                    raise AssertionError('"inputs" section is not complete')

    def test_inputs_declarations_to_dict(self):
        input1 = factories.InputFactory.create(key='key1', value='val1', description='Description1')
        input2 = factories.InputFactory.create(key='key2', value='val2', description='Description2')
        input3 = factories.InputFactory.create(key='key3', value='val3', description='Description3')
        expected_dict = {
            'key1': {'description': 'Description1'},
            'key2': {'description': 'Description2'},
            'key3': {'description': 'Description3'},
        }

        inputs_dict = Input.get_inputs_declaration_as_dict()

        self.assertDictEqual(expected_dict, inputs_dict)

    def test_inputs_values_to_dict(self):
        input1 = factories.InputFactory.create(key='key1', value='val1', description='Description1')
        input2 = factories.InputFactory.create(key='key2', value='val2', description='Description2')
        input3 = factories.InputFactory.create(key='key3', value='val3', description='Description3')
        expected_dict = {
            'key1': 'val1',
            'key2': 'val2',
            'key3': 'val3',
        }

        inputs_dict = Input.get_inputs_values_as_dict()

        self.assertDictEqual(expected_dict, inputs_dict)
