from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser

from . import tasks
from .models import Blueprint
from .serializers import BlueprintSerializer


class BlueprintsView(APIView):
    parser_classes = (MultiPartParser, FileUploadParser)

    def get(self, request):
        """
        # List all available blueprints
        """
        s = BlueprintSerializer(Blueprint.objects.all(), many = True)
        return Response(s.data)

    def put(self, request):
        """
        # Upload new blueprint archive
        """
        b = Blueprint.objects.create(archive = request.data["file"])
        s = BlueprintSerializer(b)
        pipe = (
            tasks.upload_blueprint.si(b.cfy_id) |
            tasks.create_deployment.si(b.cfy_id) |
            tasks.install.si(b.cfy_id)
        )
        pipe.apply_async()
        return Response(s.data, status = 201)

class BlueprintIdView(APIView):
    def get(self, request, blueprint_id):
        """
        # Return selected blueprint details
        """
        s = BlueprintSerializer(Blueprint.get(blueprint_id))
        return Response(s.data)

    def delete(self, request, blueprint_id):
        """
        # Delete selected blueprint
        """
        b = Blueprint.get(blueprint_id)
        pipe = (
            tasks.uninstall.si(b.cfy_id) |
            tasks.delete_deployment.si(b.cfy_id) |
            tasks.delete_blueprint.si(b.cfy_id)
        )
        pipe.apply_async()
        return Response(status = 202)
