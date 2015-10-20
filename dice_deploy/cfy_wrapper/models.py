import uuid
from django.db import models
from enum import Enum

class Blueprint(models.Model):
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
