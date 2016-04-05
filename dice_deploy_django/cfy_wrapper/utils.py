import yaml as yaml_lib
import tarfile
from django.conf import settings
import os
import tempfile

from cloudify_rest_client.client import CloudifyClient


def generate_archive_from_yaml(f_yaml):
    from cfy_wrapper.models import Input

    # read original yaml
    yaml_dict = yaml_lib.load(f_yaml)
    f_yaml.close()

    # add inputs section
    yaml_dict['inputs'] = Input.get_inputs_declaration_as_dict()
    if not yaml_dict['inputs']:
        del yaml_dict['inputs']

    f_tmp_yaml = tempfile.NamedTemporaryFile('w', delete=True)
    yaml_lib.dump(yaml_dict, f_tmp_yaml, default_flow_style=False)

    # pack everything to .tar.gz
    f_tmp = tempfile.NamedTemporaryFile('w', delete=True)
    with tarfile.open(fileobj=f_tmp, mode='w:gz') as tar:
        # add the yaml
        tar.add(f_tmp_yaml.name,
                arcname=os.path.join(settings.ARCHIVE_FOLDER_NAME, settings.YAML_NAME))
        # add common archive files
        for filename in os.listdir(settings.BLUEPRINT_PACKAGE_DIR):
            tar.add(
                os.path.join(settings.BLUEPRINT_PACKAGE_DIR, filename),
                arcname=os.path.join(settings.ARCHIVE_FOLDER_NAME, os.path.basename(filename))
            )
    f_tmp.flush()

    # close tmp files that we no longer need
    f_tmp_yaml.close()

    # return opened temporary file with archive in it
    return f_tmp


def get_cfy_client():
    if settings.MOCKUP_CFY:
        raise settings.MOCKUP_CFY

    return CloudifyClient(settings.CFY_MANAGER_URL)
