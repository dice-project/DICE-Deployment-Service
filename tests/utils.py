import base64

from cloudify_rest_client.client import CloudifyClient


def get_cfy_client(settings):

    creds = "{}:{}".format(settings.CLOUDIFY_USERNAME,
                           settings.CLOUDIFY_PASSWORD)
    creds_enc = base64.urlsafe_b64encode(creds.encode("utf-8"))
    headers = {"Authorization": "Basic {}".format(creds_enc)}
    return CloudifyClient(settings.CLOUDIFY_ADDRESS, headers=headers)
