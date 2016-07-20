import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.db import IntegrityError, transaction

from . import tasks
from .models import Blueprint, Container, Input
from .serializers import (
    BlueprintSerializer,
    ContainerSerializer,
    InputSerializer,
)
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer

logger = logging.getLogger("views")


class HeartBeatView(APIView):

    permission_classes = (AllowAny,)

    def get(self, request):
        """
        View that should be used to test service liveness
        """
        return Response({"msg": "DICE Deployment Service Heart Beat"})


class CeleryDebugView(APIView):
    """
    View that should be used to test Celery
    """

    permission_classes = (AllowAny,)

    def get(self, request):
        tasks.debug_task.apply_async()
        return Response({"msg": "Celery debug"})


class ContainersView(APIView):
    """
    Manage containers.
    """

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
        ---
        output_serializer: cfy_wrapper.serializers.ContainerSerializer
        parameters:
            - name: description
              description: Container description
              required: true
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

    def get(self, request, id):
        """
        Get container details.
        ---
        output_serializer: cfy_wrapper.serializers.ContainerSerializer
        """
        container = Container.get(id)
        s = ContainerSerializer(container)
        return Response(s.data)

    def delete(self, request, id):
        """
        Remove virtual container
        ---
        responseMessages:
            - code: 400
              message: Cannot delete container with existing blueprint
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
        ---
        responseMessages:
            - code: 400
              message: No blueprint present in container
            - code: 404
              message: Container does not exist
        """
        c = Container.get(id)
        if c.blueprint is None:
            return Response({"detail": "No blueprint uploaded yet"},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(BlueprintSerializer(c.blueprint).data)

    def post(self, request, id):
        """
        Upload blueprint to container and begin deployment flow.
        ---
        parameters:
            - name: file
              description: Must be .tar.gz file with blueprint or yaml file.
              required: true
              type: file
        responseMessages:
            - code: 202
              message: Blueprint deployment has started
            - code: 400
              message: Invalid upload
            - code: 404
              message: Container does not exist
            - code: 409
              message: Container is busy
        """
        container = Container.get(id)

        try:
            upload = request.data["file"]
        except KeyError:
            return Response({"detail": "No file uploaded"},
                            status=status.HTTP_400_BAD_REQUEST)

        blueprint = Blueprint.objects.create()
        blueprint.store_content(upload)
        if not blueprint.is_valid():
            blueprint.delete()
            return Response({"detail": "Upload is invalid"},
                            status=status.HTTP_400_BAD_REQUEST)

        success, msg = tasks.sync_container(container, blueprint)

        if success:
            return Response(ContainerSerializer(container).data,
                            status=status.HTTP_202_ACCEPTED)
        blueprint.delete()
        return Response({"detail": msg}, status=status.HTTP_409_CONFLICT)

    def delete(self, request, id):
        """
        Undeploy blueprint and delete it from container
        ---
        omit_serializer: true
        responseMessages:
            - code: 202
              message: Blueprint undeployment has started
            - code: 400
              message: No blueprint present in container
            - code: 404
              message: Container does not exists
            - code: 409
              message: Container is busy
        """
        container = Container.get(id)
        if container.blueprint is None:
            return Response({"detail": "No blueprint present"},
                            status=status.HTTP_400_BAD_REQUEST)
        success, msg = tasks.sync_container(container, None)

        if success:
            return Response(ContainerSerializer(container).data,
                            status=status.HTTP_202_ACCEPTED)
        return Response({"detail": msg}, status=status.HTTP_409_CONFLICT)

    def put(self, request, id):
        """
        Redeploy blueprint which is within this container.
        ---
        responseMessages:
            - code: 404
              message: No blueprint to redeploy
        """
        return Response({"detail": "PUT not implemented yet"},
                        status=status.HTTP_501_NOT_IMPLEMENTED)


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
        ---
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
              required: true
              type: string
        post:
            consumes:
                - application/json
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
