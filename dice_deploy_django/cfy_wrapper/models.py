import uuid
from django.db import models
from rest_framework.exceptions import NotFound
from enum import IntEnum, unique
from django.db import IntegrityError
from jsonfield import JSONField
import utils
import shutil
import os
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


# make sure every user gets authentication token on create
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


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

        @classmethod
        def all_values(cls):
            return [v.value for v in list(cls)]

        @classmethod
        def all_choices(cls):
            return [(v.value, v.name) for v in list(cls)]

    # Fields
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    state = models.IntegerField(default=State.pending.value, choices=State.all_choices())
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
                try:
                    os.makedirs(os.path.dirname(archive_filename_full))
                except OSError:
                    pass
                shutil.copy(f_tmp.name, archive_filename_full)
                self.archive = archive_filename
                self.save()

            # close the temporary file
            f_tmp.close()

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

    @property
    def errors(self):
        return self.error_set.all().order_by('-created_date')


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


class Error(models.Model):
    blueprint = models.ForeignKey(Blueprint)
    state = models.IntegerField(choices=Blueprint.State.all_choices(),
                                help_text='What state this error occured in')
    message = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def log_for_blueprint(blueprint, exception_obj):
        """ Creates and saves Error instance for blueprint and given exception. """
        err = Error()
        err.blueprint = blueprint
        err.state = blueprint.state
        err.message = str(exception_obj)
        err.save()

    @property
    def state_name(self):
        return Blueprint.State(self.state).name
