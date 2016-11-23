from django.shortcuts import render
from django.conf import settings


def index(request):
    return render(request, 'index.html', {
        'NG_BASE_URL': settings.ANGULAR_ENDPOINT.strip('/'),
        'NG_STATIC_URL': '/%s' % settings.STATIC_URL.strip('/')
    })
