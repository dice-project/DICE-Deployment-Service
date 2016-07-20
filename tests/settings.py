"""
Settings for integration tests.

Tip: use the following bash command to extract the names of the
environmental variables:

grep environ settings.py | grep -oP "(?<=os\.environ\.get\(['\"])[^'\"]*"
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# information about the Cloudify Manager's access point
CLOUDIFY_ADDRESS = os.environ.get('CLOUDIFY_ADDRESS')
CLOUDIFY_USERNAME = os.environ.get('CLOUDIFY_USERNAME', '')
CLOUDIFY_PASSWORD = os.environ.get('CLOUDIFY_PASSWORD', '')

# Target platform: 'fco', 'openstack'
TARGET_PLATFORM = os.environ.get('TARGET_PLATFORM', 'fco')

# Blueprint inputs file
INPUTS_FILE_PATH = os.path.join(os.path.dirname(BASE_DIR),
                                "inputs-{}.yaml".format(TARGET_PLATFORM))

# Settings for integration tests against deployment service
DEPLOYMENT_SERVICE_ADDRESS = os.environ.get('DEPLOYMENT_SERVICE_ADDRESS', '')
DEPLOYMENT_SERVICE_USERNAME = os.environ.get('DEPLOYMENT_SERVICE_USERNAME', '')
DEPLOYMENT_SERVICE_PASSWORD = os.environ.get('DEPLOYMENT_SERVICE_PASSWORD', '')

# Local overrides
try:
    from local_settings import *  # noqa
except ImportError:
    pass
