import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser
from rest_framework import status
from django.db import IntegrityError

from . import tasks
from .models import Blueprint, Container
from .serializers import BlueprintSerializer, ContainerSerializer

logger = logging.getLogger("views")


class DebugView(APIView):
    def get(self, request):
        logger.debug("Executed debug view")
        tasks.debug_task.delay()
        return Response({"msg": "DEBUG EXECUTED"})


class BlueprintsView(APIView):
    parser_classes = (MultiPartParser, FileUploadParser)

    def get(self, request):
        """
        List all available blueprints
        """
        s = BlueprintSerializer(Blueprint.objects.all(), many=True)
        return Response(s.data)


class BlueprintIdView(APIView):
    def get(self, request, blueprint_id):
        """
        Return selected blueprint details
        """
        s = BlueprintSerializer(Blueprint.get(blueprint_id))
        return Response(s.data)

    def delete(self, request, blueprint_id):
        """
        Delete selected blueprint
        """
        blueprint = Blueprint.get(blueprint_id)
        blueprint.pipe_undeploy_blueprint()
        return Response(status=status.HTTP_202_ACCEPTED)


class ContainersView(APIView):
    def get(self, request):
        """
        List all virtual containers and their status information
        """
        contaiers = Container.objects.all()
        s = ContainerSerializer(contaiers, many=True)
        return Response(data=s.data)

    def post(self, request):
        container = Container()
        container.save()  # all default is good
        s = ContainerSerializer(container)
        return Response(data=s.data, status=status.HTTP_201_CREATED)


class ContainerIdView(APIView):
    def get(self, request, container_id):
        """
        Display the status information about the selected virtual container
        """
        container = Container.get(container_id)
        s = ContainerSerializer(container)
        return Response(s.data)

    def delete(self, request, container_id):
        """
        Remove virtual container and undeploy its blueprint.
        """
        container = Container.get(container_id)
        try:
            container.delete()
        except IntegrityError, e:
            return Response({'msg': e.message}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ContainerBlueprint(APIView):
    def post(self, request, container_id):
        cont = Container.get(container_id)
        blueprint_old = cont.blueprint
        blueprint_new = Blueprint.objects.create(archive=request.data["file"])

        # bind new blueprint to this container
        cont.blueprint = blueprint_new
        cont.save()

        # deploy the new blueprint
        blueprint_new.pipe_deploy_blueprint()

        # undeploy the old blueprint
        if blueprint_old:
            # TODO: keep container-blueprint binding to old blueprint until cloudify undeploys it
            blueprint_old.pipe_undeploy_blueprint()

        cont_ser = ContainerSerializer(cont).data
        return Response(cont_ser, status=status.HTTP_202_ACCEPTED)






