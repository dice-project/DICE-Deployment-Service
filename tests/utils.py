import os
import base64

from cloudify_rest_client.client import CloudifyClient

TERMINAL_STATUSES = {"terminated", "failed", "cancelled"}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_cfy_client():
    creds = "{}:{}".format(os.environ["TEST_CFY_MANAGER_USERNAME"],
                           os.environ["TEST_CFY_MANAGER_PASSWORD"])
    creds_enc = base64.urlsafe_b64encode(creds.encode("utf-8"))
    headers = {"Authorization": "Basic {}".format(creds_enc)}
    return CloudifyClient(os.environ["TEST_CFY_MANAGER"], headers=headers)
