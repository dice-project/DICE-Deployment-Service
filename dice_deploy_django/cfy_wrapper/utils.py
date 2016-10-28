from cloudify_rest_client.client import CloudifyClient
from django.conf import settings

import tarfile
import base64
import stat
import os

FILE_PERMISSIONS = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
FOLDER_PERMISSIONS = (FILE_PERMISSIONS |
                      stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def extract_archive(archive, destination):
    """
    Extract arhive contents while removing toplevel prefix. If this is not
    really an archive, return False and Error message, else True.

    Safety checks:
     - make sure that no file contains full path
     - make sure there are onyl files and dirs in tarball
     - each component must be in some subfolder
     - there is only one toplevel folder
    """
    assert os.path.isdir(destination), "Destination folder is missing"

    try:
        with tarfile.open(fileobj=archive) as tar:
            members = []
            toplevel = None
            for member in tar.getmembers():
                path = os.path.normpath(member.name).split(os.sep)
                if path[0] == "":
                    return False, "Absolute path in tarball"
                if not (member.isdir() or member.isfile()):
                    return False, "Tarball can only contain files and folders"
                if len(path) == 1 and member.isfile():
                    return False, "Tarbal must have toplevel folder"
                if toplevel is None and member.isdir():
                    toplevel = path[0]
                if toplevel is not None and toplevel != path[0]:
                    return False, "More than one toplevel folder in tarball"
                member.name = os.sep.join(path[1:])
                members.append(member)

            # If we came here, tarball is ready to be extracted
            for member in members:
                tar.extract(member, destination)
            change_permissions(destination, FOLDER_PERMISSIONS,
                               FILE_PERMISSIONS)
            return True, "All OK"
    except:
        return False, "Invalid tarball"


def change_permissions(root, folder_permissions, file_permissions):
    """
    Recursively change root's permissions. This also changes the permissions
    of folder that has been passed in.

    :param root: full path to folder
    :param file_permissions: permissions that will be set on files
    :param folder_permissions: permissions that will be set on folders
    """
    assert os.path.isdir(root)

    for prefix, folders, files in os.walk(root, topdown=False):
        for file in files:
            os.chmod(os.path.join(prefix, file), file_permissions)
        for folder in folders:
            os.chmod(os.path.join(prefix, folder), folder_permissions)
    os.chmod(root, folder_permissions)


def create_archive(archive, folder):
    """
    Create tar.gz archive of selected folder.
    """
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(folder, arcname=os.path.basename(folder))


def get_cfy_client():
    creds = "{}:{}".format(settings.CFY_MANAGER_USERNAME,
                           settings.CFY_MANAGER_PASSWORD)
    creds_enc = base64.urlsafe_b64encode(creds.encode("utf-8"))
    headers = {"Authorization": "Basic {}".format(creds_enc)}
    return CloudifyClient(settings.CFY_MANAGER_URL, headers=headers)
