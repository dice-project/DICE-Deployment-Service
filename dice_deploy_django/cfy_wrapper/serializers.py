import re
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
    def validate_key(self, key):
        if not re.compile('[0-9a-z_\-]+').match(key):
            raise serializers.ValidationError('Key must be lowercase alphanumeric.')
        return key

    class Meta:
        model = Input
        fields = ("key", "value", "description")


class InputUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Input
        fields = ("key", "value", "description")
        read_only_fields = ("key",)
