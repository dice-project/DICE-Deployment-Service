from .base import BaseTest

from django.core.urlresolvers import resolve, Resolver404


class UrlTest(BaseTest):

    def _test_path(self, path, name):
        resolver = resolve(path)
        self.assertEqual(resolver.view_name, name)
        resolver = resolve(path + "/")
        self.assertEqual(resolver.view_name, name)

    def _test_bad_path(self, path):
        with self.assertRaises(Resolver404):
            resolve(path)

    def test_heartbeat(self):
        self._test_path("/heartbeat", "heartbeat")

    def test_containers(self):
        self._test_path("/containers", "containers")

    def test_single_container(self):
        self._test_path("/containers/0987-afc", "container_id")

    def test_single_container_bad(self):
        self._test_bad_path("/containers/hh")

    def test_blueprint(self):
        self._test_path("/containers/abc/blueprint", "container_blueprint")

    def test_blueprint_bad(self):
        self._test_bad_path("/containers/jkl/blueprint/")

    def test_nodes(self):
        self._test_path("/containers/abc-123/nodes", "container_nodes")

    def test_nodes_bad(self):
        self._test_bad_path("/containers/heh/nodes")

    def test_errors(self):
        self._test_path("/containers/23467-deaf/errors", "container_errors")

    def test_errors_bad(self):
        self._test_bad_path("/containers/bad-path/errors/")

    def test_inputs(self):
        self._test_path("/inputs", "inputs")
