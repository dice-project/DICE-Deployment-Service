import factory
from cfy_wrapper.models import Container, Blueprint
from django.conf import settings


class BlueprintPendingFactory(factory.DjangoModelFactory):
    state = Blueprint.State.pending.value
    archive = factory.django.FileField(from_path=settings.TEST_FILE_BLUEPRINT_EXAMPLE_GZIP)

    class Meta:
        model = Blueprint


class BlueprintArchiveDeployedFactory(factory.DjangoModelFactory):
    state = Blueprint.State.deployed.value
    archive = factory.django.FileField(from_path=settings.TEST_FILE_BLUEPRINT_EXAMPLE_GZIP)

    class Meta:
        model = Blueprint


class BlueprintYamlDeployedFactory(factory.DjangoModelFactory):
    state = Blueprint.State.deployed.value
    yaml = factory.django.FileField(from_path=settings.TEST_FILE_BLUEPRINT_EXAMPLE_YAML)

    class Meta:
        model = Blueprint


class ContainerEmptyFactory(factory.DjangoModelFactory):
    description = 'Empty container description'

    class Meta:
        model = Container


class ContainerFullGzipFactory(factory.DjangoModelFactory):
    description = 'Full container (gzip) description'
    blueprint = factory.SubFactory(BlueprintArchiveDeployedFactory)

    class Meta:
        model = Container


class ContainerFullYamlFactory(factory.DjangoModelFactory):
    description = 'Full container (yaml) description'
    blueprint = factory.SubFactory(BlueprintYamlDeployedFactory)

    class Meta:
        model = Container





