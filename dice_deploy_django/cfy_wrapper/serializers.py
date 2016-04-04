from rest_framework import serializers, fields

from .models import Blueprint, Container, Input


class BlueprintSerializer(serializers.ModelSerializer):
    modified_date = serializers.DateTimeField(read_only=True)
    outputs = fields.JSONField()

    class Meta:
        model = Blueprint
        fields = ("state_name", "id", "modified_date", "outputs")


class ContainerSerializer(serializers.ModelSerializer):
    blueprint = BlueprintSerializer()
    modified_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Container
        fields = ("id", "description", "blueprint", "modified_date")


class InputSerializer(serializers.ModelSerializer):

    class Meta:
        model = Input
        fields = ("key", "value", "description")
