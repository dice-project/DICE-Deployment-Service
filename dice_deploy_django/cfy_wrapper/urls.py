from django.conf.urls import url

from .views import (
    APIDocView,

    HeartBeatView,
    CeleryDebugView,

    ContainersView,
    ContainerIdView,
    ContainerBlueprintView,
    ContainerNodesView,

    InputsView,

    BlueprintsView,
    BlueprintIdView,
    BlueprintOutputsView,
)

urlpatterns = [
    # Docs
    url(r"^docs/?$",
        APIDocView.as_view(), name="docs"),

    # Heartbeat
    url(r"^heartbeat/?$",
        HeartBeatView.as_view(), name="heartbeat"),
    url(r"^celery/?$",
        CeleryDebugView.as_view(), name="celery"),

    # Containers
    url(r"^containers/?$",
        ContainersView.as_view(), name="containers"),
    url(r"^containers/(?P<id>[0-9a-f-]+)/?$",
        ContainerIdView.as_view(), name="container_id"),
    url(r"^containers/(?P<id>[0-9a-f-]+)/blueprint?$",
        ContainerBlueprintView.as_view(), name="container_blueprint"),
    url(r"^containers/(?P<id>[0-9a-f-]+)/nodes?$",
        ContainerNodesView.as_view(), name="container_nodes"),

    # Inputs
    url(r"^inputs/?$",
        InputsView.as_view(), name="inputs"),

    # Compatibility routes - not really needed, but part of public API
    url(r"^blueprints/?$",
        BlueprintsView.as_view(), name="blueprints"),
    url(r"^blueprints/(?P<blueprint_id>[0-9a-f-]+)/?$",
        BlueprintIdView.as_view(), name="blueprint_id"),
    url(r"^blueprints/(?P<blueprint_id>[0-9a-f-]+)/outputs/?$",
        BlueprintOutputsView.as_view(), name="blueprint_outputs"),
]
