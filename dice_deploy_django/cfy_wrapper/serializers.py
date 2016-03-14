from rest_framework import serializers

from .models import Blueprint, Container


class BlueprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blueprint
        fields = ("state_name", "cfy_id")


class ContainerSerializer(serializers.ModelSerializer):
    blueprint = BlueprintSerializer()

    class Meta:
        model = Container
        fields = ("id", "blueprint")
