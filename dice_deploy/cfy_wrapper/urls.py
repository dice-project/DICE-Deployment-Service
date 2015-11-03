from django.conf.urls import url

from .views import (
    DebugView,
    BlueprintsView,
    BlueprintIdView,
)

urlpatterns = [
    url(r"^debug/?$",
        DebugView.as_view(), name = "debug"),
    url(r"^blueprints/?$",
        BlueprintsView.as_view(), name = "blueprints"),
    url(r"^blueprints/(?P<blueprint_id>[0-9a-f-]+)/?$",
        BlueprintIdView.as_view(), name = "blueprint_id"),
]
