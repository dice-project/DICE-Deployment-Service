from .base import BaseTest

from django.db import IntegrityError
from concurrency.exceptions import RecordModifiedError

import tarfile
import yaml
import os

from cfy_wrapper.models import (
    Blueprint,
    Container,
    Input,
    Error,
)


class BlueprintTest(BaseTest):

    def test_creation_and_deletion(self):
        b = Blueprint.objects.create()
        content_folder = self.wd.getpath(str(b.id))
        # Make sure blueprint is created with proper defaults and that
        # associated folder is created
        self.assertEqual(b.state, Blueprint.State.present)
        self.assertEqual(b.cfy_id, str(b.id))
        self.assertEqual(b.content_folder, content_folder)
        self.assertEqual(b.content_tar, content_folder + ".tar.gz")
        self.assertFalse(b.is_valid())
        self.wd.compare([str(b.id) + "/"])
        # Deletion should remove folder (and any created archives)
        b.delete()
        self.wd.compare(expected=())

    def test_creation_many(self):
        folders = []
        for i in range(10):
            b = Blueprint.objects.create()
            content_folder = self.wd.getpath(str(b.id))
            folders.append(str(b.id) + "/")

            self.assertEqual(b.state, Blueprint.State.present)
            self.assertEqual(b.cfy_id, str(b.id))
            self.assertEqual(b.content_folder, content_folder)
            self.assertEqual(b.content_tar, content_folder + ".tar.gz")
            self.assertFalse(b.is_valid())

        self.wd.compare(sorted(folders))

    def test_valid_blueprint_yaml(self):
        b = Blueprint.objects.create()
        self.wd.write((str(b.id), "blueprint.yaml"), b"test: pair")
        self.assertTrue(b.is_valid())

    def test_invalid_blueprint_yaml(self):
        b = Blueprint.objects.create()
        self.wd.write((str(b.id), "blueprint.yaml"), b"a: b: c")
        self.assertFalse(b.is_valid())

    def test_missing_blueprint_yaml(self):
        b = Blueprint.objects.create()
        self.wd.write((str(b.id), "sample.yaml"), b"a: b: c")
        self.assertFalse(b.is_valid())

    def test_pack(self):
        b = Blueprint.objects.create()
        self.wd.write((str(b.id), "blueprint.yaml"), b"test: pair")
        archive = b.pack()
        self.assertTrue(os.path.isfile(archive))
        with tarfile.open(archive, "r:gz") as tar:
            content = {info.name for info in tar.getmembers()}
        self.assertEqual({
            str(b.id),
            os.path.join(str(b.id), "blueprint.yaml"),
        }, content)

    def test_update_inputs_add(self):
        b = Blueprint.objects.create()
        self.wd.write((str(b.id), "blueprint.yaml"), b"test: pair")
        b.update_inputs({"new": "key"})
        with open(self.wd.getpath((str(b.id), "blueprint.yaml"))) as f:
            result = yaml.load(f)
        self.assertEqual({
            "test": "pair",
            "inputs": {
                "new": "key"
            }
        }, result)

    def test_update_inputs_replace(self):
        b = Blueprint.objects.create()
        self.wd.write((str(b.id), "blueprint.yaml"),
                      b"inputs:\n  test: pair")
        b.update_inputs({"new": "key"})
        with open(self.wd.getpath((str(b.id), "blueprint.yaml"))) as f:
            result = yaml.load(f)
        self.assertEqual({
            "inputs": {
                "new": "key"
            }
        }, result)

    def test_update_inputs_remove(self):
        b = Blueprint.objects.create()
        self.wd.write((str(b.id), "blueprint.yaml"),
                      b"key: value\ninputs:\n  test: pair")
        b.update_inputs({})
        with open(self.wd.getpath((str(b.id), "blueprint.yaml"))) as f:
            result = yaml.load(f)
        self.assertEqual({
            "key": "value"
        }, result)

    def test_update_inputs_unicode(self):
        b = Blueprint.objects.create()
        self.wd.write((str(b.id), "blueprint.yaml"), b"test: pair")
        b.update_inputs({u"new": u"key"})
        with open(self.wd.getpath((str(b.id), "blueprint.yaml"))) as f:
            raw_data = f.read()
        self.assertFalse("!!python/unicode" in raw_data)

    def test_store_content_yaml(self):
        b = Blueprint.objects.create()
        file = "test.yaml"
        content = b"key: value"
        self.wd.write(file, content)
        with open(self.wd.getpath(file)) as f:
            b.store_content(f)
        self.wd.compare(["blueprint.yaml"], path=str(b.id))
        self.assertEqual(content,
                         self.wd.read((str(b.id), "blueprint.yaml")))
        self.assertTrue(b.is_valid())

    def test_store_content_tar(self):
        b = Blueprint.objects.create()

        self.wd.write(("toplevel", "a", "file1.txt"), b"content")
        self.wd.write(("toplevel", "b", "c", "file2.txt"), b"content")
        toplevel = self.wd.getpath("toplevel")
        archive = self.wd.getpath("test.tar.gz")
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(toplevel, arcname="x/y/toplevel")

        with open(archive) as f:
            b.store_content(f)
        self.wd.compare([
            "y/",
            "y/toplevel/",
            "y/toplevel/a/",
            "y/toplevel/a/file1.txt",
            "y/toplevel/b/",
            "y/toplevel/b/c/",
            "y/toplevel/b/c/file2.txt",
        ], path=str(b.id))
        self.assertFalse(b.is_valid())

    def test_in_error(self):
        for state in list(Blueprint.State):
            b = Blueprint.objects.create(state=state)
            self.assertFalse(b.in_error)
            b = Blueprint.objects.create(state=-state)
            self.assertTrue(b.in_error)

    def test_state_name(self):
        for state in list(Blueprint.State):
            b = Blueprint.objects.create(state=state)
            self.assertEqual(b.state_name, state.name)
            b = Blueprint.objects.create(state=-state)
            self.assertEqual(b.state_name, state.name)

    def test_log_error_simple(self):
        msg = "Sample error"
        b = Blueprint.objects.create()

        b.log_error(msg)

        es = list(Error.objects.all())
        self.assertEqual(1, len(es))
        self.assertEqual(msg, es[0].message)
        self.assertEqual(b, es[0].blueprint)

        b.refresh_from_db()
        es = list(b.errors.all())
        self.assertEqual(1, len(es))
        self.assertEqual(msg, es[0].message)
        self.assertEqual(b, es[0].blueprint)

    def test_delete_error_on_blueprint_delete(self):
        msg = "Sample error"
        b = Blueprint.objects.create()
        b.log_error(msg)

        b.delete()

        self.assertEqual(0, Error.objects.all().count())


class ContainerTest(BaseTest):

    def test_creation_and_deletion(self):
        desc = "Sample description"
        c = Container.objects.create(description=desc)

        c = Container.get(str(c.id))
        self.assertEqual(c.description, desc)
        self.assertEqual(c.blueprint, None)

        c.delete()
        self.assertEqual([], list(Container.objects.all()))

    def test_container_deletion_valid(self):
        c = Container.objects.create()
        c.delete()
        self.assertEqual([], list(Container.objects.all()))

    def test_container_deletion_invalid(self):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        with self.assertRaises(IntegrityError):
            c.delete()
        Container.objects.get(id=c.id)
        Blueprint.objects.get(id=b.id)

    def test_prevent_blueprint_escaping_container(self):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)

        b.delete()

        c = Container.get(str(c.id))
        self.assertIsNone(c.blueprint)

    def test_concurent_modification_protection(self):
        c = Container.objects.create()
        c1 = Container.objects.get(id=c.id)
        c2 = Container.objects.get(id=c.id)
        c1.save()
        with self.assertRaises(RecordModifiedError):
            c2.save()


class InputTest(BaseTest):

    def test_creation_and_deletion(self):
        Input.objects.create(key="key", value="value", description="desc")
        i = Input.objects.get(key="key")
        i.delete()
        self.assertEqual([], list(Input.objects.all()))

    def test_fail_if_no_key(self):
        with self.assertRaises(IntegrityError):
            Input.objects.create(value="value", description="desc")

    def test_fail_if_no_value(self):
        with self.assertRaises(IntegrityError):
            Input.objects.create(key="key", description="desc")

    def test_no_description_is_empty_string(self):
        Input.objects.create(key="key", value="value")
        i = Input.objects.get(key="key")
        self.assertEqual("", i.description)

    def test_fail_if_duplicate_key(self):
        Input.objects.create(key="key", value="v1", description="dsc1")
        with self.assertRaises(IntegrityError):
            Input.objects.create(key="key", value="v2", description="dsc2")

    def test_accept_long_values(self):
        long_value_length = 5000
        text = "x" * long_value_length
        Input.objects.create(key="key", value=text, description="desc")
        self.assertEqual(text, Input.objects.get(key="key").value)

    def test_inputs_declaration(self):
        Input.objects.create(key="key1", value="value1", description="desc1")
        Input.objects.create(key="key2", value="value2", description="desc2")
        self.assertEqual({
            "key1": {"description": "desc1", "default": "value1"},
            "key2": {"description": "desc2", "default": "value2"},
        }, Input.get_inputs_declaration())


class ErrorTest(BaseTest):

    def test_creation_single(self):
        b = Blueprint.objects.create()
        msg = "Error msg"

        Error.objects.create(blueprint=b, message=msg)

        self.assertEqual(1, Error.objects.all().count())
        e = list(Error.objects.all())[0]
        self.assertEqual(e.message, msg)
        self.assertEqual(e.blueprint, b)

    def test_delete_error_on_blueprint_delete(self):
        b = Blueprint.objects.create()
        msg = "Error msg"
        Error.objects.create(blueprint=b, message=msg)

        b.delete()

        self.assertEqual(0, Error.objects.all().count())
