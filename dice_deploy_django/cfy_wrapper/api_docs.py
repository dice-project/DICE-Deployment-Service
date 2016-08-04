from rest_framework.renderers import BaseRenderer

import yaml
import json
import os


class OpenAPIRenderer(BaseRenderer):
    media_type = "application/openapi+json"
    charset = None
    format = "openapi"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return json.dumps(data).encode("utf-8")


def get_api_reference(authenticated):
    docs = os.path.join(os.path.dirname(__file__), "api.yaml")
    with open(docs) as f:
        data = yaml.load(f)
    if not authenticated:
        filter_paths(data)
    return data


def filter_paths(data):
    methods = ("delete", "get", "head", "options", "patch", "post", "put")
    paths = data["paths"]
    for path, path_data in paths.items():
        for method in methods:
            if method not in path_data:
                continue
            method_data = path_data[method]
            if method_data.get("x-needs-login", True):
                del path_data[method]
        if len(path_data) == 0:
            del paths[path]
