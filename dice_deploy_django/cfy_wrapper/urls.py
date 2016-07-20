from django.conf.urls import url

from .views import (
    HeartBeatView,
    CeleryDebugView,

    ContainersView,
    ContainerIdView,
    ContainerBlueprintView,

    InputsView,
)

urlpatterns = [
    # Heartbeat
    url(r"^heartbeat/?$",
        HeartBeatView.as_view(), name="heartbeat"),
    url(r"^debug/?$",
        CeleryDebugView.as_view(), name="celery"),

    # Containers
    url(r"^containers/?$",
        ContainersView.as_view(), name="containers"),
    url(r"^containers/(?P<id>[0-9a-f-]+)/?$",
        ContainerIdView.as_view(), name="container_id"),
    url(r"^containers/(?P<id>[0-9a-f-]+)/blueprint?$",
        ContainerBlueprintView.as_view(), name="container_blueprint"),

    # Inputs
    url(r"^inputs/?$",
        InputsView.as_view(), name="inputs"),
]
