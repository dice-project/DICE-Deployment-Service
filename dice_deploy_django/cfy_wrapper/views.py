import logging
import json

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser
from rest_framework import status
from django.db import IntegrityError

from . import tasks
from .models import Blueprint, Container
from .serializers import BlueprintSerializer, ContainerSerializer
from .forms import BlueprintUploadForm

logger = logging.getLogger("views")


class DebugView(APIView):
    def get(self, request):
        """
        Debug view for testing celery.
        """
        logger.debug("Executed debug view")
        tasks.debug_task.delay()
        return Response({"msg": "DEBUG EXECUTED"})


class BlueprintsView(APIView):
    parser_classes = (MultiPartParser, FileUploadParser)

    def get(self, request):
        """
        List all available blueprints.
        ---
        serializer: cfy_wrapper.serializers.BlueprintSerializer
        """
        s = BlueprintSerializer(Blueprint.objects.all(), many=True)
        return Response(s.data)


class BlueprintIdView(APIView):
    def get(self, request, blueprint_id):
        """
        Get blueprint details.
        ---
        serializer: cfy_wrapper.serializers.BlueprintSerializer
        """
        s = BlueprintSerializer(Blueprint.get(blueprint_id))
        return Response(s.data)

    def delete(self, request, blueprint_id):
        """
        Delete selected blueprint
        ---
        omit_serializer: true
        """
        blueprint = Blueprint.get(blueprint_id)
        blueprint.pipe_undeploy_blueprint()
        return Response(status=status.HTTP_202_ACCEPTED)


class BlueprintOutputsView(APIView):
    def get(self, request, blueprint_id):
        """
        Get outputs that this blueprint produc
        ---
        """
        blueprint = Blueprint.get(blueprint_id)
        outputs = tasks.get_outputs(blueprint)
        return Response({'outputs': outputs})


class ContainersView(APIView):
    def get(self, request):
        """
        List all containers with their blueprints.
        ---
        serializer: cfy_wrapper.serializers.ContainerSerializer
        """
        contaiers = Container.objects.all()
        s = ContainerSerializer(contaiers, many=True)
        return Response(data=s.data)

    def post(self, request):
        """
        Create empty container.
        ---
        output_serializer: cfy_wrapper.serializers.ContainerSerializer
        parameters:
            - name: description
              description: Container description
              required: false
              type: string
        omit_parameters:
            - blueprint

        """
        container = Container()
        container.description = request.data.get('description', None)
        container.save()  # all default is good

        container.refresh_from_db()
        s = ContainerSerializer(container)
        return Response(data=s.data, status=status.HTTP_201_CREATED)


class ContainerIdView(APIView):
    def get(self, request, container_id):
        """
        Get container details.
        ---
        output_serializer: cfy_wrapper.serializers.ContainerSerializer
        """
        container = Container.get(container_id)
        s = ContainerSerializer(container)
        return Response(s.data)

    def delete(self, request, container_id):
        """
        Remove virtual container and undeploy its blueprint.
        ---
        responseMessages:
            - code: 400
              message: Cannot delete container with existing blueprint
        """
        container = Container.get(container_id)
        try:
            container.delete()
        except IntegrityError, e:
            return Response({'msg': e.message}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ContainerBlueprint(APIView):
    def post(self, request, container_id):
        """
        Upload blueprint to container and begin deployment flow.
        ---
        parameters:
            - name: file
              description: Must be .tar.gz file with blueprint.
              required: true
              type: file
        """
        file_uploaded = request.data.get('file')
        form = BlueprintUploadForm(files={'archive': file_uploaded, 'yaml': file_uploaded})

        if form.is_valid():
            cont = Container.get(container_id)
            blueprint_old = cont.blueprint
            blueprint_new = form.instance

            # bind new blueprint to this container
            cont.blueprint = blueprint_new
            cont.save()

            # deploy the new blueprint
            blueprint_new.pipe_deploy_blueprint()

            cont_ser = ContainerSerializer(cont).data
            return Response(cont_ser, status=status.HTTP_202_ACCEPTED)

        return Response({'msg': form.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, container_id):
        """
        Redeploy blueprint which is within this container.
        ---
        responseMessages:
            - code: 404
              message: No blueprint to redeploy
        """
        cont = Container.get(container_id)
        blueprint = cont.blueprint

        if not blueprint:
            return Response({'msg': 'No blueprint to redeploy'}, status=status.HTTP_404_NOT_FOUND)

        # redeploy the blueprint
        blueprint.pipe_redeploy_blueprint()

        cont_ser = ContainerSerializer(cont).data
        return Response(cont_ser, status=status.HTTP_202_ACCEPTED)





