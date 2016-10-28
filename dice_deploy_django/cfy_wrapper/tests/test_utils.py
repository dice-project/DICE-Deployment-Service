from .base import BaseTest

from cfy_wrapper import utils

import tarfile
import stat
import os


class ExtractArchiveTest(BaseTest):

    def test_valid_extraction(self):
        # Prepare files
        self.wd.write(("toplevel", "a", "file1.txt"), b"content")
        self.wd.write(("toplevel", "b", "c", "file2.txt"), b"content")
        toplevel = self.wd.getpath("toplevel")
        # Setup archive
        archive = self.wd.getpath("test.tar.gz")
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(toplevel, arcname="x/y/toplevel")
        # Test validness
        self.wd.makedir("result")
        result = self.wd.getpath("result")
        with open(archive, "rb") as tar:
            self.assertTrue(utils.extract_archive(tar, result)[0])
        # Test proper extraction
        self.wd.compare([
            "y/",
            "y/toplevel/",
            "y/toplevel/a/",
            "y/toplevel/a/file1.txt",
            "y/toplevel/b/",
            "y/toplevel/b/c/",
            "y/toplevel/b/c/file2.txt",
        ], path="result")

    def test_invalid_tar(self):
        # Prepare files
        file = "test.txt"
        self.wd.write(file, b"test_content")
        # Test invalidness
        with open(self.wd.getpath(file), "rb") as tar:
            self.assertFalse(utils.extract_archive(tar, self.wd.path)[0])

    def test_no_toplevel(self):
        # Prepare files
        file = "test.txt"
        self.wd.write(file, b"test_content")
        # Setup archive
        archive = self.wd.getpath("test.tar.gz")
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(self.wd.getpath(file), arcname=file)
        # Test invalidness
        with open(archive, "rb") as tar:
            self.assertFalse(utils.extract_archive(tar, self.wd.path)[0])

    def test_multiple_toplevels(self):
        # Prepare files
        files = ["file1", "file2", "file3"]
        for file in files:
            self.wd.write((file, file + ".txt"), b"test_content")
        # Setup archive
        archive = self.wd.getpath("test.tar.gz")
        with tarfile.open(archive, "w:gz") as tar:
            for file in files:
                tar.add(self.wd.getpath(file), arcname=file)
        # Test invalidness
        with open(archive, "rb") as tar:
            self.assertFalse(utils.extract_archive(tar, self.wd.path)[0])

    def test_absolute_path(self):
        # This filter is needed to force absolute names in archive
        def filter(info):
            info.name = "/" + info.name
            return info

        # Prepare files
        file = self.wd.getpath("test.txt")
        self.wd.write("test.txt", b"test_content")
        # Setup archive
        archive = self.wd.getpath("test.tar.gz")
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(file, filter=filter)
        # Test invalidness
        with open(archive, "rb") as tar:
            self.assertFalse(utils.extract_archive(tar, self.wd.path)[0])

    def test_missing_destination(self):
        # Prepare files
        self.wd.write(("toplevel", "file1.txt"), b"content")
        toplevel = self.wd.getpath("toplevel")
        # Setup archive
        archive = self.wd.getpath("test.tar.gz")
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(toplevel, arcname="toplevel")
        # Test validness
        result = self.wd.getpath("result")
        with open(archive, "rb") as tar:
            with self.assertRaises(AssertionError):
                utils.extract_archive(tar, result)


class ChangePermissionsTest(BaseTest):

    # Test tree:
    #
    #   a/
    #   +-- b/
    #   |   `-- 1.txt
    #   +-- c/
    #   |   +-- d/
    #   |   |   +-- 4.txt
    #   |   `-- 3.txt
    #   +-- e/
    #   +-- f/
    #   `-- 2.txt
    FOLDERS = ['a', 'a/b', 'a/c', 'a/c/d', 'a/e', 'a/f']
    FILES = ['a/b/1.txt', 'a/2.txt', 'a/c/3.txt', 'a/c/d/4.txt']

    # Permissions tha we are setting during test
    FOLDER_PERMISSIONS = stat.S_IRWXU | stat.S_IROTH
    FILE_PERMISSIONS = stat.S_IRWXU | stat.S_IWOTH

    def setUp(self):
        super(ChangePermissionsTest, self).setUp()

        # Create test folder tree
        for d in self.FOLDERS:
            self.wd.makedir(d)
            os.chmod(self.wd.getpath(d), stat.S_IRWXU)
        for f in self.FILES:
            self.wd.write(f, 'MOCK')
            os.chmod(self.wd.getpath(d), stat.S_IRWXU)

    def _get_permission_snapshot(self):
        def get_perms(path):
            full_path = self.wd.getpath(path)
            return stat.S_IMODE(os.stat(full_path).st_mode)

        return (
            {d: get_perms(d) for d in self.FOLDERS},
            {f: get_perms(f) for f in self.FILES}
        )

    def _run(self, path):
        utils.change_permissions(self.wd.getpath(path),
                                 self.FOLDER_PERMISSIONS,
                                 self.FILE_PERMISSIONS)

    # Actual tests
    def test_missing_path(self):
        with self.assertRaises(AssertionError):
            self._run(self.wd.getpath('NON_EXISTENT'))

    def test_file(self):
        with self.assertRaises(AssertionError):
            self._run(self.wd.getpath('a/2.txt'))

    def test_empty_dir(self):
        old_folder_perms, old_file_perms = self._get_permission_snapshot()
        old_folder_perms['a/e'] = self.FOLDER_PERMISSIONS

        self._run('a/e')

        new_folder_perms, new_file_perms = self._get_permission_snapshot()
        self.assertEqual(old_folder_perms, new_folder_perms)
        self.assertEqual(old_file_perms, new_file_perms)

    def test_dir_with_files_only(self):
        old_folder_perms, old_file_perms = self._get_permission_snapshot()
        old_folder_perms['a/b'] = self.FOLDER_PERMISSIONS
        old_file_perms['a/b/1.txt'] = self.FILE_PERMISSIONS

        self._run('a/b')

        new_folder_perms, new_file_perms = self._get_permission_snapshot()
        self.assertEqual(old_folder_perms, new_folder_perms)
        self.assertEqual(old_file_perms, new_file_perms)

    def test_subtree(self):
        old_folder_perms, old_file_perms = self._get_permission_snapshot()
        old_folder_perms['a/c'] = self.FOLDER_PERMISSIONS
        old_folder_perms['a/c/d'] = self.FOLDER_PERMISSIONS
        old_file_perms['a/c/3.txt'] = self.FILE_PERMISSIONS
        old_file_perms['a/c/d/4.txt'] = self.FILE_PERMISSIONS

        self._run('a/c')

        new_folder_perms, new_file_perms = self._get_permission_snapshot()
        self.assertEqual(old_folder_perms, new_folder_perms)
        self.assertEqual(old_file_perms, new_file_perms)

    def test_complete_tree(self):
        old_folder_perms = {k: self.FOLDER_PERMISSIONS for k in self.FOLDERS}
        old_file_perms = {k: self.FILE_PERMISSIONS for k in self.FILES}

        self._run('a')

        new_folder_perms, new_file_perms = self._get_permission_snapshot()
        self.assertEqual(old_folder_perms, new_folder_perms)
        self.assertEqual(old_file_perms, new_file_perms)


class CreateArchiveTest(BaseTest):

    def test_valid_creation(self):
        # Prepare files
        self.wd.write(("toplevel", "a", "file1.txt"), b"content")
        self.wd.write(("toplevel", "b", "c", "file2.txt"), b"content")
        toplevel = self.wd.getpath("toplevel")
        # Setup archive
        archive = self.wd.getpath("test.tar.gz")
        # Test creation
        utils.create_archive(archive, toplevel)
        # Check contents
        with tarfile.open(archive, "r:gz") as tar:
            members = {info.name for info in tar.getmembers()}
        self.assertEqual({
            "toplevel",
            "toplevel/a",
            "toplevel/a/file1.txt",
            "toplevel/b",
            "toplevel/b/c",
            "toplevel/b/c/file2.txt",
        }, members)

    def test_missing_folder(self):
        archive = self.wd.getpath("test.tar.gz")
        toplevel = self.wd.getpath("non-existing-folder")
        with self.assertRaises(OSError):
            utils.create_archive(archive, toplevel)

    def test_overwrite_archive(self):
        self.wd.write("test.tar.gz", b"sample_content")
        self.wd.write(("toplevel", "a", "file1.txt"), b"content")
        toplevel = self.wd.getpath("toplevel")
        archive = self.wd.getpath("test.tar.gz")
        utils.create_archive(archive, toplevel)
        with tarfile.open(archive, "r:gz") as tar:
            members = {info.name for info in tar.getmembers()}
        self.assertEqual({
            "toplevel",
            "toplevel/a",
            "toplevel/a/file1.txt",
        }, members)
