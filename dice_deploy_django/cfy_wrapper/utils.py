import yaml as yaml_lib
import tarfile
from django.conf import settings
import os
import tempfile

from cloudify_rest_client.client import CloudifyClient


def generate_archive_from_yaml(f_yaml):
    """
    Generates temporary file that contains .tar.gz archive with prepared blueprint package.
    Inputs section in original yaml is overwriten with inputs from database prior archiving.
    :param f_yaml: opened .yaml file (in read mode)
    :return: temporary .tar.gz file that is deleted upon closing
    """
    from cfy_wrapper.models import Input

    # read original yaml
    yaml_dict = yaml_lib.load(f_yaml)
    f_yaml.close()

    # add/overwrite inputs section
    with tempfile.NamedTemporaryFile('w', delete=True) as f_tmp_yaml:
        yaml_dict['inputs'] = Input.get_inputs_declaration_as_dict()
        if not yaml_dict['inputs']:
            del yaml_dict['inputs']
        yaml_lib.safe_dump(yaml_dict, f_tmp_yaml, default_flow_style=False)

        def set_permissions(tarinfo):
            tarinfo.mode = 0777
            return tarinfo

        # pack everything to .tar.gz archive
        f_tmp = tempfile.NamedTemporaryFile('w', delete=True)
        with tarfile.open(fileobj=f_tmp, mode='w:gz') as tar:
            # add the yaml
            tar.add(f_tmp_yaml.name, filter=set_permissions,
                    arcname=os.path.join(settings.ARCHIVE_FOLDER_NAME, settings.YAML_NAME))
        f_tmp.flush()

    # return opened temporary file with archive in it
    return f_tmp


def get_cfy_client():
    if settings.MOCKUP_CFY:
        raise settings.MOCKUP_CFY

    return CloudifyClient(settings.CFY_MANAGER_URL)
