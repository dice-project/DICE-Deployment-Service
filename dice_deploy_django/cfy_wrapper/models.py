import uuid
from django.db import models
from rest_framework.exceptions import NotFound
from enum import Enum
from django.db import IntegrityError
from jsonfield import JSONField
import utils
import shutil
import os
from django.conf import settings


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
    class State(Enum):
        # deployment flow
        pending = 1
        uploaded = 2
        ready_to_deploy = 3
        preparing_deploy = 4
        working = 5
        deployed = 6
        # undeploymen flow
        uninstalling = 101
        deleting_deployment = 102
        deleting_blueprint = 103
        # special states
        undeployed = 0  # exists on gui, but not on cfy manageer
        error = -1

    # Fields
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    state = models.IntegerField(default=State.pending.value)
    archive = models.FileField(upload_to="blueprints_targz", blank=True, null=True)
    yaml = models.FileField(upload_to="blueprints_yaml", blank=True, null=True)
    outputs = JSONField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    @property
    def cfy_id(self):
        return str(self.id)

    @property
    def state_name(self):
        return Blueprint.State(self.state).name

    def generate_archive(self):
        """
        Generate archive for this blueprint. Does nothing if archive was originally uploaded
        instead of yaml.
        NOTE: This overrides previously generated archive
        :return: filepath to the generated file
        """
        if bool(self.yaml):
            # generate archive
            f_tmp = utils.generate_archive_from_yaml(self.yaml.file)

            # store it under same archive name as the old one if exists ...
            if bool(self.archive):
                archive_filename = self.archive.name
                os.remove(archive_filename)
                shutil.copy(f_tmp.name, archive_filename)
            # ... or create new one
            else:
                archive_filename = os.path.join('generated_archives', str(uuid.uuid4()) + '.tar.gz')
                archive_filename_full = os.path.join(settings.MEDIA_ROOT, archive_filename)
                os.makedirs(os.path.dirname(archive_filename_full))
                shutil.copy(f_tmp.name, archive_filename_full)
                self.archive = archive_filename
                self.save()

        return os.path.join(settings.MEDIA_ROOT, self.archive.name)

    def pipe_deploy_blueprint(self):
        """ Defines and starts async pipeline for deploying blueprint to cloudify """
        from cfy_wrapper import tasks

        # update my state immediately
        self.state = Blueprint.State.pending.value
        self.save()

        pipe = (
            tasks.upload_blueprint.si(self.cfy_id) |
            tasks.create_deployment.si(self.cfy_id) |
            tasks.install.si(self.cfy_id)
        )
        pipe.apply_async()

    def pipe_undeploy_blueprint(self):
        """ Defines and starts async pipeline for undeploying blueprint from cloudify """
        from cfy_wrapper import tasks

        # update my state immediately
        self.state = Blueprint.State.uninstalling.value
        self.save()

        pipe = (
            tasks.uninstall.si(self.cfy_id) |
            tasks.delete_deployment.si(self.cfy_id) |
            tasks.delete_blueprint.si(self.cfy_id, delete_local=False)
        )
        pipe.apply_async()

    def pipe_redeploy_blueprint(self):
        """ Defines and starts async pipeline for redeploying blueprint on cloudify """
        from cfy_wrapper import tasks

        # prevent undeploying when I'm not even deployed
        if self.state != self.State.deployed.value:
            return self.pipe_deploy_blueprint()

        # update my state immediately
        self.state = Blueprint.State.uninstalling.value
        self.save()

        pipe = (
            # undeploy
            tasks.uninstall.si(self.cfy_id) |
            tasks.delete_deployment.si(self.cfy_id) |
            tasks.delete_blueprint.si(self.cfy_id, delete_local=False) |
            # deploy
            tasks.upload_blueprint.si(self.cfy_id) |
            tasks.create_deployment.si(self.cfy_id) |
            tasks.install.si(self.cfy_id)
        )
        pipe.apply_async()


class Container(Base):
    # Fields
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    description = models.CharField(max_length=512, blank=True, null=True)
    blueprint = models.ForeignKey(Blueprint, null=True, blank=True, on_delete=models.SET_NULL)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def delete(self, using=None, keep_parents=False):
        if self.blueprint:
            if self.blueprint.state in [Blueprint.State.undeployed.value,
                                        Blueprint.State.error.value]:
                self.blueprint.delete()
            else:
                raise IntegrityError('Cannot delete container with existing blueprint')
        super(Container, self).delete(using, keep_parents)
