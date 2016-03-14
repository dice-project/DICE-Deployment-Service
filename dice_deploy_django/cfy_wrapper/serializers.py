from rest_framework import serializers, fields

from .models import Blueprint, Container


class BlueprintSerializer(serializers.ModelSerializer):
    modified_date = serializers.DateTimeField(read_only=True)
    outputs = fields.JSONField()

    class Meta:
        model = Blueprint
        fields = ("state_name", "cfy_id", "modified_date", "outputs")


class ContainerSerializer(serializers.ModelSerializer):
    blueprint = BlueprintSerializer()
    modified_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Container
        fields = ("id", "description", "blueprint", "modified_date")
