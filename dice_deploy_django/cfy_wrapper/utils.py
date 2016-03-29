import yaml as yaml_lib
import tarfile
from django.conf import settings
import os
import tempfile


def generate_archive_from_yaml(f_yaml):

    # add inputs section to yaml
    # TODO
    # close the yaml
    f_yaml.close()
    # pack everything to .tar.gz
    f_tmp = tempfile.NamedTemporaryFile('w', delete=True)
    with tarfile.open(fileobj=f_tmp, mode='w:gz') as tar:
        tar.add(f_yaml.name, arcname=os.path.basename(f_yaml.name))
        for filename in os.listdir(settings.BLUEPRINT_PACKAGE_DIR):
            tar.add(
                os.path.join(settings.BLUEPRINT_PACKAGE_DIR, filename),
                arcname=os.path.basename(filename)
            )
    f_tmp.flush()
    # return opened temporary file with archive in it
    return f_tmp


