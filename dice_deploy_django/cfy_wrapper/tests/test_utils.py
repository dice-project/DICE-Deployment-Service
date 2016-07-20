from .base import BaseTest

from cfy_wrapper import utils

import tarfile


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
