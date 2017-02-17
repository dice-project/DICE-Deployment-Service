from enum import IntEnum, unique

from rest_framework.exceptions import NotFound

from django.utils.encoding import python_2_unicode_compatible
from django.conf import settings
from django.db import IntegrityError
from django.db import models

from jsonfield import JSONField
from concurrency.fields import IntegerVersionField

from dsl_parser import parser

from . import utils

import uuid
import yaml
import os


class Base(models.Model):
    @classmethod
    def get(cls, str_id):
        try:
            obj = cls.objects.get(pk=uuid.UUID(str_id))
        except (ValueError, cls.DoesNotExist):
            msg = "{} '{}' does not exist".format(cls.__name__, str_id)
            raise NotFound(msg)
        return obj

    class Meta:
        abstract = True


@python_2_unicode_compatible
class Blueprint(Base):
    # Possible states
    @unique
    class State(IntEnum):
        """
        Blueprint states

        States roughly correspond to the states of the Cloudify, but we made
        them a bit more fine grained to support wider variety of recovery
        actions without user intervention (for example, if user wishes to
        remove existing blueprint that failed to validate, no uninstall should
        be done).

        Error states are negated states from this enum (for example, -2 means
        that blueprint could not be uploaded to cloudify). Not all negations
        make sense, but we allow them in order to make code a bit more
        generic.
        """
        present = 1  # This is initial state + after uninstall finishes

        # Installation
        uploading_to_cloudify = 2
        uploaded_to_cloudify = 3
        preparing_deployment = 4
        prepared_deployment = 5
        installing = 6
        installed = 7  # This is what we reach after install workflow finishes
        fetching_outputs = 8

        deployed = 9  # This is idle state

        # Uninstall workflow
        uninstalling = 10
        uninstalled = 11
        deleting_deployment = 12
        deleted_deployment = 13
        deleting_from_cloudify = 14

    # Fields
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    state = models.IntegerField(default=State.present.value)
    outputs = JSONField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    @property
    def cfy_id(self):
        return str(self.id)

    @property
    def state_name(self):
        return Blueprint.State(abs(self.state)).name

    @property
    def in_error(self):
        return self.state < 0

    @property
    def content_folder(self):
        return os.path.join(settings.MEDIA_ROOT, self.cfy_id)

    @property
    def content_blueprint(self):
        return os.path.join(self.content_folder, "blueprint.yaml")

    @property
    def content_tar(self):
        return self.content_folder + ".tar.gz"

    def store_content(self, content):
        """
        First, try to untar the content. If this fails, simply copy the file
        to content folder. This function does no validation of blueprints!
        """
        if not utils.extract_archive(content, self.content_folder)[0]:
            path = os.path.join(self.content_folder, "blueprint.yaml")
            with open(path, "w") as file:
                file.write(content.read())

    def is_valid(self):
        """
        Each blueprint needs blueprint.yaml in folder. If this file does not
        exist, we are grumpy.
        """
        if not os.path.isfile(self.content_blueprint):
            return False, "File 'blueprint.yaml' is missing"

        try:
            with open(self.content_blueprint) as f:
                yaml.safe_load(f)
            return True, "All ok for now"
        except:
            return False, "Blueprint file is not valid yaml"

    def pack(self):
        """
        Create tarball that contains complete blueprint contents, augmented
        with admin supplied inputs.
        """
        utils.create_archive(self.content_tar, self.content_folder)
        return self.content_tar

    def log_error(self, msg):
        """
        Log error for this blueprint
        """
        self.errors.create(message=msg)

    def prepare_inputs(self):
        """
        Obtain blueprint inputs and report error on missing database inputs

        Blueprint can contain two different kinds of inputs: optional and
        mandatory. Blueprint inputs that contain "default" field are optional,
        all other inputs are mandatory.

        In order to properly respect user's overrides of default values, we
        try to load all inputs that are listed in blueprint from database. But
        when checking for proper set of inputs, we only make sure mandatory
        inputs are covered, since optional inputs have default value and
        deploy doesn't need them set explicitly.
        """

        blueprint = self.content_blueprint
        blueprint_inputs = parser.parse_from_path(blueprint).get("inputs", {})
        blueprint_keys = blueprint_inputs.keys()
        required_blueprint_keys = {
            k for k, v in blueprint_inputs.items() if "default" not in v
        }

        input_filter = dict(key__in=blueprint_keys)
        service_inputs = {
            i.key: i.value for i in Input.objects.filter(**input_filter)
        }
        service_keys = set(service_inputs.keys())

        diff = required_blueprint_keys - service_keys
        if len(diff) > 0:
            return False, diff
        return True, service_inputs

    def __str__(self):
        return "id: {}, state: {}, in_error: {}".format(
            self.id, self.state_name, self.in_error
        )


class ContainerQuerySet(models.QuerySet):
    """
    This query set is here just to make deletion slow and safe;)
    """
    def delete(self, *args, **kwargs):
        for obj in self:
            obj.delete()


@python_2_unicode_compatible
class Container(Base):
    objects = ContainerQuerySet.as_manager()

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    description = models.TextField()
    blueprint = models.ForeignKey(Blueprint, null=True, blank=True,
                                  on_delete=models.SET_NULL,
                                  related_name="container")
    queue = models.ForeignKey(Blueprint, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="+")
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    busy = models.BooleanField(default=False)

    # Optimistic concurrency protection
    version = IntegerVersionField()

    @property
    def cfy_id(self):
        return str(self.id)

    def delete(self, *args, **kwargs):
        if self.blueprint is not None:
            msg = "Cannot delete container with existing blueprint"
            raise IntegrityError(msg)
        if self.busy:
            msg = "Cannot delete busy container"
            raise IntegrityError(msg)
        super(Container, self).delete(*args, **kwargs)

    def __str__(self):
        return "id: {}, blueprint: {}, queue: {}, busy: {}".format(
            self.id, getattr(self.blueprint, "id", "none"),
            getattr(self.queue, "id", "none"), self.busy
        )


@python_2_unicode_compatible
class Input(models.Model):
    key = models.CharField(max_length=256, primary_key=True)
    value = models.TextField(null=True)
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if self.key is None or self.key == "":
            raise IntegrityError("Key cannot be empty")
        if self.value is None:
            raise IntegrityError("Value cannot be empty")
        super(Input, self).save(*args, **kwargs)

    @staticmethod
    def get_inputs_declaration():
        """
        Reads all Inputs from database and forms a dict with their declaration.
        :return: dict that should be added to blueprint.yaml
        """
        return {el.key: {
            "description": el.description,
            "default": el.value
        } for el in Input.objects.all()}

    def __str__(self):
        return "{}: {}".format(self.key, self.value)


@python_2_unicode_compatible
class Error(models.Model):

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    message = models.TextField()
    blueprint = models.ForeignKey(Blueprint, on_delete=models.CASCADE,
                                  related_name="errors")
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "id: {}, msg: {}, blueprint: {}".format(
            self.id, self.message, self.blueprint.id
        )
