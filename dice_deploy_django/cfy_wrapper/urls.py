from django.conf.urls import url, include

from .views import (
    DebugView,
    BlueprintsView,
    BlueprintIdView,
    ContainersView,
    ContainerIdView,
    ContainerBlueprint,
    BlueprintOutputsView
)

urlpatterns = [
    url(r'^docs/?', include('rest_framework_swagger.urls')),  # swagger
    url(r"^debug/?$",
        DebugView.as_view(), name="debug"),
    # blueprint
    url(r"^blueprints/?$",
        BlueprintsView.as_view(), name="blueprints"),
    url(r"^blueprints/(?P<blueprint_id>[0-9a-f-]+)/?$",
        BlueprintIdView.as_view(), name="blueprint_id"),
    url(r"^blueprints/(?P<blueprint_id>[0-9a-f-]+)/outputs?$",
        BlueprintOutputsView.as_view(), name="blueprint_outputs"),
    # container
    url(r"^containers/?$",
        ContainersView.as_view(), name="containers"),
    url(r"^containers/(?P<container_id>[0-9a-f-]+)/?$",
        ContainerIdView.as_view(), name="container_id"),
    url(r"^containers/(?P<container_id>[0-9a-f-]+)/blueprint?$",
        ContainerBlueprint.as_view(), name="container_blueprint"),
]
