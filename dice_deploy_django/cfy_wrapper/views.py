import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from django.shortcuts import get_object_or_404

from . import tasks, utils
from .models import Blueprint, Container, Input
from .serializers import BlueprintSerializer, ContainerSerializer, InputSerializer, \
    InputUpdateSerializer
from .forms import BlueprintUploadForm
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer

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
        containers = Container.objects.all()
        container_id = self.request.query_params.get('id', None)
        if container_id is not None:
            containers = containers.filter(id=container_id)
        s = ContainerSerializer(containers, many=True)
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


class ContainerIdNodesView(APIView):
    def get(self, request, container_id):
        """
        Get ip addresses of machines, running in selected deployment
        ---
        parameters:
            - name: raw
              description: Return bare array of ip addreses
              type: string
              paramType: query
        """
        container = Container.get(container_id)
        data = []
        if container.blueprint is not None:
            client = utils.get_cfy_client()
            instances = client.node_instances.list(
                deployment_id=container.blueprint.cfy_id,
            )
            instances = [i for i in instances if "ip" in i.runtime_properties]
            data = [{
                "node_id": i.node_id,
                "id": i.id,
                "ip": i.runtime_properties["ip"]
            } for i in instances]
            if "raw" in request.query_params:
                data = [d["ip"] for d in data]
        return Response(data)


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


class InputsView(APIView):

    def get(self, request):
        """
        List all available inputs.
        ---
        serializer: cfy_wrapper.serializers.InputSerializer
        """
        s = InputSerializer(Input.objects.all(), many=True)
        return Response(s.data)

    def post(self, request):
        """
        Create new input.
        ---
        serializer: cfy_wrapper.serializers.InputSerializer
        parameters:
            - name: key
              description: input unique name
              required: true
              type: string
            - name: value
              description: input value
              required: true
              type: string
            - name: description
              description: input description
              required: false
              type: string
        post:
            consumes:
                - application/json
        """
        s = InputSerializer(data=request.data)
        if s.is_valid(raise_exception=True):
            s.save()
        return Response(data=s.data, status=status.HTTP_201_CREATED)


class InputIdView(APIView):
    def get(self, request, input_key):
        """
        Retrieve input
        ---
        serializer: cfy_wrapper.serializers.InputSerializer
        """
        input = get_object_or_404(Input, pk=input_key)
        s = InputSerializer(input)
        return Response(s.data)

    def delete(self, request, input_key):
        """
        Delete input
        ---
        """
        input = get_object_or_404(Input, pk=input_key)
        input.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, input_key):
        """
        Update input value and description. Key cannot be updated.
        ---
        serializer: cfy_wrapper.serializers.InputUpdateSerializer
        """
        input = get_object_or_404(Input, pk=input_key)
        s = InputUpdateSerializer(data=request.data, instance=input)
        if s.is_valid(raise_exception=True):
            s.save()
        return Response(s.data)


class AuthTokenView(APIView):
    permission_classes = ()

    def post(self, request):
        """
        Retrieve authorization token.
        ---
        serializer: rest_framework.authtoken.serializers.AuthTokenSerializer
        """
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'username': user.username,
            'token': token.key
        })


