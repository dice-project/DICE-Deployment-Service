from enum import IntEnum, unique

from rest_framework.exceptions import NotFound

from django.conf import settings
from django.db import IntegrityError
from django.db import models

from jsonfield import JSONField
from concurrency.fields import IntegerVersionField

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
        fetched_outputs = 9  # This is idle state
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
        try:
            with open(self.content_blueprint) as f:
                yaml.safe_load(f)
            return True
        except:
            return False

    def pack(self):
        """
        Create tarball that contains complete blueprint contents, augmented
        with admin supplied inputs.
        """
        utils.create_archive(self.content_tar, self.content_folder)
        return self.content_tar

    def update_inputs(self, inputs):
        """
        This function loads blueprint yaml, replaces inputs section and saves
        blueprint back.
        """
        with open(self.content_blueprint) as file:
            data = yaml.load(file)
        if len(inputs) == 0 and "inputs" in data:
            del data["inputs"]
        else:
            data.update({"inputs": inputs})
        with open(self.content_blueprint, "w") as file:
            yaml.dump(data, file)

    @property
    def errors(self):
        return self.error_set.all().order_by('-created_date')


class ContainerQuerySet(models.QuerySet):
    """
    This query set is here just to make deletion slow and safe;)
    """
    def delete(self, *args, **kwargs):
        for obj in self:
            obj.delete()


class Container(Base):
    objects = ContainerQuerySet.as_manager()

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    description = models.TextField()
    blueprint = models.ForeignKey(Blueprint, null=True, blank=True,
                                  on_delete=models.SET_NULL, related_name="+")
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


class Input(models.Model):
    key = models.CharField(max_length=256, primary_key=True)
    value = models.TextField()
    description = models.CharField(max_length=512, blank=True, null=True)

    @staticmethod
    def get_inputs_declaration_as_dict():
        """
        Reads all Inputs from database and forms a dict with their declaration.
        :return: dict that should be added to blueprint.yaml
        """
        return {str(el.key): {str('description'): str(el.description) if el.description else ''}
                for el in Input.objects.all()}

    @staticmethod
    def get_inputs_values_as_dict():
        """
        Reads all Inputs from database and forms a dict of key-value pairs.
        :return: dict that should be passed to create_deployment cfy call
        """
        return {el.key: el.value for el in Input.objects.all()}
