from django.conf.urls import url, include

from .views import (
    DebugView,
    BlueprintsView,
    BlueprintIdView,
    ContainersView,
    ContainerIdView,
    ContainerIdErrorsView,
    ContainerIdNodesView,
    ContainerBlueprint,
    BlueprintOutputsView,
    InputsView,
    InputIdView
)

urlpatterns = [
    url(r"^debug/?$",
        DebugView.as_view(), name="debug"),
    # blueprint
    url(r"^blueprints/?$",
        BlueprintsView.as_view(), name="blueprints"),
    url(r"^blueprints/(?P<blueprint_id>[0-9a-f-]+)/?$",
        BlueprintIdView.as_view(), name="blueprint_id"),
    url(r"^blueprints/(?P<blueprint_id>[0-9a-f-]+)/outputs/?$",
        BlueprintOutputsView.as_view(), name="blueprint_outputs"),
    # container
    url(r"^containers/?$",
        ContainersView.as_view(), name="containers"),
    url(r"^containers/(?P<container_id>[0-9a-f-]+)/?$",
        ContainerIdView.as_view(), name="container_id"),
    url(r"^containers/(?P<container_id>[0-9a-f-]+)/errors/?$",
        ContainerIdErrorsView.as_view(), name="container_id_errors"),
    url(r"^containers/(?P<container_id>[0-9a-f-]+)/nodes/?$",
        ContainerIdNodesView.as_view(), name="container_id_nodes"),
    url(r"^containers/(?P<container_id>[0-9a-f-]+)/blueprint?$",
        ContainerBlueprint.as_view(), name="container_blueprint"),
    # inputs
    url(r"^inputs/?$",
        InputsView.as_view(), name="inputs"),
    url(r"^inputs/(?P<input_key>[0-9a-z_\-]+)?$",
        InputIdView.as_view(), name="input_id"),
]
