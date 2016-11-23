from cfy_wrapper.urls import urlpatterns as cfy_urls
from cfy_wrapper.views import AuthTokenView
from cfy_wrapper_gui.urls import urlpatterns as cfy_gui_urls
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.conf.urls import url, include

admin.autodiscover()

urlpatterns = [
    url(r'^admin/?', include(admin.site.urls)),
    url(r'^auth/get-token/?', AuthTokenView.as_view(), name='get_token')
]
urlpatterns += cfy_urls
urlpatterns += cfy_gui_urls
