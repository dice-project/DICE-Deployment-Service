from cfy_wrapper.urls import urlpatterns as cfy_urls
from cfy_wrapper_gui.urls import urlpatterns as cfy_gui_urls
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = cfy_urls
urlpatterns += cfy_gui_urls
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
