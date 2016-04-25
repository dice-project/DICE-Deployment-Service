from cfy_wrapper.urls import urlpatterns as cfy_urls
from cfy_wrapper_gui.urls import urlpatterns as cfy_gui_urls
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.conf.urls import url, include
from rest_framework.authtoken import views as token_views

admin.autodiscover()

urlpatterns = [
    url(r'^docs/?', include('rest_framework_swagger.urls')),  # swagger
    url(r'^admin/?', include(admin.site.urls)),
    url(r'^auth/get-token/?', token_views.obtain_auth_token)
]
urlpatterns += cfy_urls
urlpatterns += cfy_gui_urls

if settings.GUNICORN_STATICS:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
else:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
