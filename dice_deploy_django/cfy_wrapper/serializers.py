import collections

from rest_framework import serializers

from .models import Blueprint, Container, Input, Error


class ErrorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Error
        fields = ("id", "created", "message")


class BlueprintSerializer(serializers.ModelSerializer):

    class Meta:
        model = Blueprint
        fields = ("id", "state_name", "modified_date", "outputs",
                  "in_error", "errors")

    outputs = serializers.JSONField(read_only=True)
    errors = ErrorSerializer(read_only=True, many=True)

    def save(*args, **kwargs):
        raise RuntimeError("Blueprint saving is not supported")

    def update(*args, **kwargs):
        raise RuntimeError("Blueprint updating is not supported")


class ContainerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Container
        fields = ("id", "description", "blueprint", "modified_date", "busy")
        read_only_fields = ("busy",)

    blueprint = BlueprintSerializer(read_only=True)


class InputListSerializer(serializers.ListSerializer):

    def validate(self, data):
        keys = [input["key"] for input in data]
        if len(keys) == len(set(keys)):
            return super(InputListSerializer, self).validate(data)

        # Prepare decent error message here
        counter = collections.Counter(keys)
        dups = [k for k, c in counter.items() if c > 1]
        raise serializers.ValidationError("Duplicated keys: {}".format(dups))


class InputSerializer(serializers.ModelSerializer):

    class Meta:
        model = Input
        fields = ("key", "value", "description")
        list_serializer_class = InputListSerializer

    value = serializers.CharField()


class VMSerializer(serializers.Serializer):

    id = serializers.CharField()
    node_id = serializers.CharField()
    ip = serializers.CharField()
    components = serializers.ListField()
