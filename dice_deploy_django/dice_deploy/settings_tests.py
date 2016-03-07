from dice_deploy.settings import *
import os

# tests will check this flag pripr running
IS_TEST_SETTINGS = True

TEST_FILES_DIR = os.path.join(BASE_DIR, 'unit_tests', 'files')
TEST_FILE_BLUEPRINT_EXAMPLE = os.path.join(TEST_FILES_DIR, 'blueprints', 'example_blueprint.tar.gz')

MEDIA_ROOT = os.path.join(BASE_DIR, "uploads_tests")

# make celery synchronous
# CELERY_ALWAYS_EAGER = True
CELERY_APP_NAME = 'dice_deploy_tests'