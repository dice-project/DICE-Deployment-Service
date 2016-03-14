import factory
from cfy_wrapper.models import Container, Blueprint
from django.conf import settings


class BlueprintPendingFactory(factory.DjangoModelFactory):
    state = Blueprint.State.pending.value
    archive = factory.django.FileField(from_path=settings.TEST_FILE_BLUEPRINT_EXAMPLE)

    class Meta:
        model = Blueprint


class BlueprintDeployedFactory(factory.DjangoModelFactory):
    state = Blueprint.State.deployed.value
    archive = factory.django.FileField(from_path=settings.TEST_FILE_BLUEPRINT_EXAMPLE)

    class Meta:
        model = Blueprint


class ContainerEmptyFactory(factory.DjangoModelFactory):
    description = 'Empty container description'

    class Meta:
        model = Container


class ContainerFullFactory(factory.DjangoModelFactory):
    description = 'Full container description'
    blueprint = factory.SubFactory(BlueprintDeployedFactory)

    class Meta:
        model = Container



