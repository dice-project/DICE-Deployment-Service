import logging

from rest_framework_swagger.renderers import SwaggerUIRenderer

from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from django.db import IntegrityError, transaction

from . import tasks
from . import utils
from .models import Blueprint, Container, Input
from .serializers import (
    BlueprintSerializer,
    ContainerSerializer,
    InputSerializer,
    VMSerializer,
    ErrorSerializer,
)
from .api_docs import OpenAPIRenderer, get_api_reference

logger = logging.getLogger("views")


class APIDocView(APIView):

    permission_classes = (AllowAny,)
    renderer_classes = (SwaggerUIRenderer, OpenAPIRenderer)

    def get(self, request):
        schema = get_api_reference(request.auth is not None)
        return Response(schema)


class HeartBeatView(APIView):

    permission_classes = (AllowAny,)

    def get(self, request):
        """
        View that should be used to test service liveness
        """
        return Response({"msg": "DICE Deployment Service Heart Beat"})


class ContainersView(APIView):

    def get(self, request):
        containers = Container.objects.all()
        container_id = self.request.query_params.get('id', None)
        if container_id is not None:
            containers = containers.filter(id=container_id)
        s = ContainerSerializer(containers, many=True)
        return Response(data=s.data)

    def post(self, request):
        """
        Create empty container.
        """
        s = ContainerSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data, status=status.HTTP_201_CREATED)


class ContainerIdView(APIView):

    def get(self, request, id):
        """
        Get container details.
        """
        container = Container.get(id)
        s = ContainerSerializer(container)
        return Response(s.data)

    def delete(self, request, id):
        """
        Remove virtual container
        """
        container = Container.get(id)
        try:
            container.delete()
        except IntegrityError as e:
            return Response({'detail': e.message},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ContainerBlueprintView(APIView):

    def get(self, request, id):
        """
        Show information about blueprint that is uploaded to container
        """
        c = Container.get(id)
        if c.blueprint is None:
            return Response({"detail": "No blueprint uploaded yet"},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(BlueprintSerializer(c.blueprint).data)

    def post(self, request, id):
        """
        Upload blueprint to container and begin deployment flow.
        """
        container = Container.get(id)

        try:
            upload = request.data["file"]
        except KeyError:
            return Response({"detail": "No file uploaded"},
                            status=status.HTTP_400_BAD_REQUEST)

        blueprint = Blueprint.objects.create()
        blueprint.store_content(upload)

        success, msg = blueprint.is_valid()
        if not success:
            blueprint.delete()
            return Response({"detail": msg},
                            status=status.HTTP_400_BAD_REQUEST)

        register_param = request.query_params.get("register_app", "")
        register_app = register_param.lower() == "true"
        success, msg = tasks.sync_container(container, blueprint, register_app)

        if not success:
            blueprint.delete()
            return Response({"detail": msg}, status=status.HTTP_409_CONFLICT)

        return Response(BlueprintSerializer(blueprint).data,
                        status=status.HTTP_202_ACCEPTED)

    def delete(self, request, id):
        """
        Undeploy blueprint and delete it from container
        """
        container = Container.get(id)
        if container.blueprint is None:
            return Response({"detail": "No blueprint present"},
                            status=status.HTTP_400_BAD_REQUEST)
        success, msg = tasks.sync_container(container, None, False)

        if success:
            return Response(BlueprintSerializer(container.blueprint).data,
                            status=status.HTTP_202_ACCEPTED)
        return Response({"detail": msg}, status=status.HTTP_409_CONFLICT)

    def put(self, request, id):
        """
        Redeploy blueprint which is within this container.
        """
        return Response({"detail": "PUT not implemented yet"},
                        status=status.HTTP_501_NOT_IMPLEMENTED)


class ContainerNodesView(APIView):

    @staticmethod
    def _gen_node(data):
        return dict(id=data.id, node_id=data.node_id, components=[],
                    ip=data.runtime_properties["ip"])

    def get(self, request, id):
        """
        List VMs that are running inside selected container. Each node also
        contains set of components that are installed onto it.
        """
        container = Container.get(id)
        if container.blueprint is None:
            return Response([])

        client = utils.get_cfy_client()
        nodes = client.nodes.list(container.blueprint.cfy_id)
        instances = client.node_instances.list(container.blueprint.cfy_id)

        node_types = {n.id: n.type for n in nodes}
        vms = {i.id: self._gen_node(i) for i in instances if i.id == i.host_id}
        for i in instances:
            if i.host_id is not None:
                vms[i.host_id]["components"].append(node_types[i.node_id])

        s = VMSerializer(vms.values(), many=True)
        return Response(s.data)


class ContainerErrorsView(APIView):

    def get(self, request, id):
        """
        Return errors for selected container.
        """
        container = Container.get(id)
        if container.blueprint is None:
            return Response([])
        errors = ErrorSerializer(container.blueprint.errors, many=True)
        return Response(errors.data)


class InputsView(APIView):

    def get(self, request):
        """
        List all available inputs.
        """
        s = InputSerializer(Input.objects.all(), many=True)
        return Response(s.data)

    def post(self, request):
        """
        Add new inputs to deployment service. Note that uploading new set of
        inputs will delete all existing inputs. You have been warned.
        """
        s = InputSerializer(data=request.data, many=True)
        with transaction.atomic():
            Input.objects.all().delete()
            s.is_valid(raise_exception=True)
            s.save()
            return Response(data=s.data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        """
        Deletes all inputs from service
        """
        Input.objects.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuthTokenView(APIView):

    permission_classes = (AllowAny,)

    def post(self, request):
        """
        Retrieve authorization token.
        """
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'username': user.username,
            'token': token.key
        })


# Backwards compatibility API views
class BlueprintsView(APIView):

    def get(self, request):
        s = BlueprintSerializer(Blueprint.objects.all(), many=True)
        return Response(s.data)


class BlueprintIdView(APIView):

    def get(self, request, blueprint_id):
        s = BlueprintSerializer(Blueprint.get(blueprint_id))
        return Response(s.data)

    def delete(self, request, blueprint_id):
        containers = list(Blueprint.get(blueprint_id).container.all())
        if len(containers) != 1:
            return Response({"detail": "Blueprint not deployed"},
                            status=status.HTTP_409_CONFLICT)

        container = containers[0]
        success, msg = tasks.sync_container(container, None)

        if success:
            return Response(BlueprintSerializer(container.blueprint).data,
                            status=status.HTTP_202_ACCEPTED)
        return Response({"detail": msg}, status=status.HTTP_409_CONFLICT)


class BlueprintOutputsView(APIView):

    def get(self, request, blueprint_id):
        blueprint = Blueprint.get(blueprint_id)
        return Response({"outputs": blueprint.outputs})
