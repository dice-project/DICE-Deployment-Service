from django.conf.urls import url

from .views import (
    DebugView,
    BlueprintsView,
    BlueprintIdView,
    ContainersView,
    ContainerIdView,
    ContainerBlueprint
)

urlpatterns = [
    url(r"^debug/?$",
        DebugView.as_view(), name="debug"),
    # blueprint
    url(r"^blueprints/?$",
        BlueprintsView.as_view(), name="blueprints"),
    url(r"^blueprints/(?P<blueprint_id>[0-9a-f-]+)/?$",
        BlueprintIdView.as_view(), name="blueprint_id"),
    # container
    url(r"^containers/?$",
        ContainersView.as_view(), name="containers"),
    url(r"^containers/(?P<container_id>[0-9a-f-]+)/?$",
        ContainerIdView.as_view(), name="container_id"),
    url(r"^containers/(?P<container_id>[0-9a-f-]+)/blueprints?$",
        ContainerBlueprint.as_view(), name="container_blueprint"),
]
