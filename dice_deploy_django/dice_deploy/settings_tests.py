from dice_deploy.settings import *
import os

# tests will check this flag pripr running
IS_TEST_SETTINGS = True

# This is needed since same settings is used with 'test' (by calling dice_deploy REST API)
# command and 'directly' (by Celery worker).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "test_db.sqlite3"),
        "TEST": {
            "NAME": os.path.join(BASE_DIR, "test_db.sqlite3"),
        }
    }
}

TEST_FILES_DIR = os.path.join(BASE_DIR, 'unit_tests', 'files')
TEST_FILES_TMP_DIR = os.path.join(TEST_FILES_DIR, 'tmp')
TEST_FILE_BLUEPRINT_EXAMPLE_GZIP = os.path.join(TEST_FILES_DIR, 'blueprints', 'example_blueprint.tar.gz')
TEST_FILE_BLUEPRINT_EXAMPLE_YAML = os.path.join(TEST_FILES_DIR, 'blueprints', 'example_blueprint.yaml')

MEDIA_ROOT = os.path.join(BASE_DIR, "uploads_tests")

# make celery synchronous
# CELERY_ALWAYS_EAGER = True

CELERY_DEFAULT_QUEUE = 'dice_deploy_tests'

MOCKUP_CFY = MOCKUP_CFY_OPTION_YES_SUCCESS  # selected option
