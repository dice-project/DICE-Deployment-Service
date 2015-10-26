import uuid
from django.db import models
from rest_framework.exceptions import NotFound
from enum import Enum


class Base(models.Model):
    @classmethod
    def get(cls, str_id):
        try:
            obj = cls.objects.get(pk = uuid.UUID(str_id))
        except (ValueError, cls.DoesNotExist):
            msg = "{} '{}' does not exist".format(cls.__name__, str_id)
            raise NotFound(msg)
        return obj

    class Meta:
        abstract = True


class Blueprint(Base):
    # Possible states
    State = Enum("State", "pending uploaded ready_to_deploy deployed")

    # Fields
    id = models.UUIDField(
        primary_key = True, default = uuid.uuid4, editable = False
    )
    state = models.IntegerField(default = State.pending.value)
    archive = models.FileField(upload_to = "blueprints")

    @property
    def cfy_id(self):
        return str(self.id)

    @property
    def state_name(self):
        return Blueprint.State(self.status).name
