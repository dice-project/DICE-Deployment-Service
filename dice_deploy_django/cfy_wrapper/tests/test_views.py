from .base import BaseViewTest, date2str, identity, Field

from cfy_wrapper.models import Blueprint, Container, Input
from cfy_wrapper.views import (
    HeartBeatView,
    ContainersView,
    ContainerIdView,
    ContainerBlueprintView,
    InputsView,
)

from django.core.urlresolvers import reverse
from rest_framework.response import Response
from rest_framework import status

import mock
import json
import io

CONTAINER_FIELDS = (
    Field("id", str, "id"),
    Field("description", identity, "description"),
    Field("modified_date", date2str, "modified_date"),
    # Blueprint field is tested separatelly
)

BLUEPRINT_FIELDS = (
    Field("cfy_id", identity, "id"),
    Field("state_name", identity, "state_name"),
    Field("modified_date", date2str, "modified_date"),
    Field("outputs", identity, "outputs")
)

INPUT_FIELDS = (
    Field("key", identity, "key"),
    Field("value", identity, "value"),
    Field("description", identity, "description"),
)


class HeartBeatTest(BaseViewTest):

    def test_alive_no_auth(self):
        req = self.get(reverse("heartbeat"), auth=False)
        resp = HeartBeatView.as_view()(req)
        self.assertEqual(status.HTTP_200_OK, resp.status_code)

    def test_alive_auth(self):
        req = self.get(reverse("heartbeat"), auth=True)
        resp = HeartBeatView.as_view()(req)
        self.assertEqual(status.HTTP_200_OK, resp.status_code)


class ContainersTest(BaseViewTest):

    def test_not_auth(self):
        req = self.get(reverse("containers"), auth=False)
        resp = ContainersView.as_view()(req)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, resp.status_code)

    @mock.patch.object(ContainersView, "get", return_value=Response({}))
    def test_get_route(self, mock_method):
        url = reverse("containers")
        self.client.get(url)
        mock_method.assert_called_once()

    def test_get_empty(self):
        cs = [Container.objects.create() for _ in range(4)]
        req = self.get(reverse("containers"), auth=True)

        resp = ContainersView.as_view()(req)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.compare(CONTAINER_FIELDS, resp.data, cs)
        for item in resp.data:
            self.assertIsNone(item["blueprint"])

    def test_get_render_empty(self):
        cs = [Container.objects.create() for _ in range(3)]
        url = reverse("containers")

        resp = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        data = json.loads(resp.content)
        self.compare(CONTAINER_FIELDS, data, cs)
        for item in data:
            self.assertIsNone(item["blueprint"])

    def test_get_non_empty(self):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        req = self.get(reverse("containers"), auth=True)

        resp = ContainersView.as_view()(req)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.compare(CONTAINER_FIELDS, resp.data, c)
        self.compare(BLUEPRINT_FIELDS, resp.data[0]["blueprint"], b)

    def test_get_render_non_empty(self):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        url = reverse("containers")

        resp = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        data = json.loads(resp.content)
        self.compare(CONTAINER_FIELDS, data, c)
        self.compare(BLUEPRINT_FIELDS, data[0]["blueprint"], b)

    def test_get_no_containers(self):
        req = self.get(reverse("containers"), auth=True)

        resp = ContainersView.as_view()(req)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual([], resp.data)

    def test_get_no_containers_render(self):
        url = reverse("containers")

        resp = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        data = json.loads(resp.content)
        self.assertEqual([], data)

    @mock.patch.object(ContainersView, "post", return_value=Response({}))
    def test_post_route(self, mock_method):
        url = reverse("containers")
        self.client.post(url)
        mock_method.assert_called_once()

    def test_post(self):
        data = {"description": "sample-desc"}
        req = self.post(reverse("containers"), data, auth=True)

        resp = ContainersView.as_view()(req)

        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        c = Container.objects.all()[0]
        self.compare(CONTAINER_FIELDS, resp.data, c)
        self.assertIsNone(resp.data["blueprint"])

    def test_post_render(self):
        data = {"description": "sample-desc"}
        url = reverse("containers")

        resp = self.client.post(url, data=data)

        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        data = json.loads(resp.content)
        c = Container.objects.all()[0]
        self.compare(CONTAINER_FIELDS, data, c)
        self.assertIsNone(data["blueprint"])


class ContainerIdTest(BaseViewTest):

    def test_not_auth(self):
        kw = dict(id="abc")
        req = self.get(reverse("container_id", kwargs=kw), auth=False)
        resp = ContainerIdView.as_view()(req, **kw)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, resp.status_code)

    @mock.patch.object(ContainerIdView, "get", return_value=Response({}))
    def test_get_route(self, mock_method):
        kw = dict(id="abc")
        url = reverse("container_id", kwargs=kw)
        self.client.get(url)
        mock_method.assert_called_once()

    def test_get_empty(self):
        c = Container.objects.create()
        kw = dict(id=str(c.id))
        req = self.get(reverse("container_id", kwargs=kw), auth=True)

        resp = ContainerIdView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.compare(CONTAINER_FIELDS, resp.data, c)
        self.assertIsNone(resp.data["blueprint"])

    def test_get_render_empty(self):
        c = Container.objects.create()
        kw = dict(id=str(c.id))
        url = reverse("container_id", kwargs=kw)

        resp = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        data = json.loads(resp.content)
        self.compare(CONTAINER_FIELDS, data, c)
        self.assertIsNone(data["blueprint"])

    def test_get_non_empty(self):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        kw = dict(id=str(c.id))
        req = self.get(reverse("container_id", kwargs=kw), auth=True)

        resp = ContainerIdView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.compare(CONTAINER_FIELDS, resp.data, c)
        self.compare(BLUEPRINT_FIELDS, resp.data["blueprint"], b)

    def test_get_render_non_empty(self):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        kw = dict(id=str(c.id))
        url = reverse("container_id", kwargs=kw)

        resp = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        data = json.loads(resp.content)
        self.compare(CONTAINER_FIELDS, data, c)
        self.compare(BLUEPRINT_FIELDS, data["blueprint"], b)

    def test_get_no_containers(self):
        kw = dict(id="abc")
        req = self.get(reverse("container_id", kwargs=kw), auth=True)

        resp = ContainerIdView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)
        self.assertIn("detail", resp.data)

    @mock.patch.object(ContainerIdView, "delete", return_value=Response({}))
    def test_delete_route(self, mock_method):
        kw = dict(id="abc")
        url = reverse("container_id", kwargs=kw)
        self.client.delete(url)
        mock_method.assert_called_once()

    def test_delete_empty(self):
        c = Container.objects.create()
        kw = dict(id=str(c.id))
        req = self.delete(reverse("container_id", kwargs=kw), auth=True)

        resp = ContainerIdView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_204_NO_CONTENT, resp.status_code)

    def test_delete_render_empty(self):
        c = Container.objects.create()
        kw = dict(id=str(c.id))
        url = reverse("container_id", kwargs=kw)

        resp = self.client.delete(url)

        self.assertEqual(status.HTTP_204_NO_CONTENT, resp.status_code)

    def test_delete_non_empty(self):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        kw = dict(id=str(c.id))
        req = self.delete(reverse("container_id", kwargs=kw), auth=True)

        resp = ContainerIdView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertIn("detail", resp.data)

    def test_delete_render_non_empty(self):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        kw = dict(id=str(c.id))
        url = reverse("container_id", kwargs=kw)

        resp = self.client.delete(url)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertIn("detail", resp.data)

    def test_delete_no_containers(self):
        kw = dict(id="abc")
        req = self.delete(reverse("container_id", kwargs=kw), auth=True)

        resp = ContainerIdView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)
        self.assertIn("detail", resp.data)


class ContainerBlueprintTest(BaseViewTest):

    def test_not_auth(self):
        kw = dict(id="abc")
        req = self.get(reverse("container_blueprint", kwargs=kw), auth=False)
        resp = ContainerBlueprintView.as_view()(req, **kw)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, resp.status_code)

    @mock.patch.object(ContainerBlueprintView, "get",
                       return_value=Response({}))
    def test_get_route(self, mock_get):
        kw = dict(id="abc")
        url = reverse("container_blueprint", kwargs=kw)
        self.client.get(url, **kw)
        mock_get.assert_called_once()

    def test_get(self):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        kw = dict(id=str(c.id))
        req = self.get(reverse("container_blueprint", kwargs=kw), auth=True)

        resp = ContainerBlueprintView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.compare(BLUEPRINT_FIELDS, resp.data, b)

    def test_get_render(self):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        kw = dict(id=str(c.id))
        url = reverse("container_blueprint", kwargs=kw)

        resp = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        data = json.loads(resp.content)
        self.compare(BLUEPRINT_FIELDS, data, b)

    def test_get_no_container(self):
        kw = dict(id="abc")
        req = self.get(reverse("container_blueprint", kwargs=kw), auth=True)

        resp = ContainerBlueprintView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)
        self.assertIn("detail", resp.data)

    def test_get_no_blueprint(self):
        c = Container.objects.create()
        kw = dict(id=str(c.id))
        req = self.get(reverse("container_blueprint", kwargs=kw), auth=True)

        resp = ContainerBlueprintView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertIn("detail", resp.data)

    @mock.patch.object(ContainerBlueprintView, "post",
                       return_value=Response({}))
    def test_post_route(self, mock_method):
        kw = dict(id="abc")
        url = reverse("container_blueprint", kwargs=kw)
        self.client.post(url)
        mock_method.assert_called_once()

    def test_post_no_file(self):
        c = Container.objects.create()
        kw = dict(id=str(c.id))
        req = self.post(reverse("container_blueprint", kwargs=kw),
                        data=None, auth=True)

        resp = ContainerBlueprintView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertIn("detail", resp.data)
        self.assertIsNone(c.blueprint)
        self.assertEqual(0, Blueprint.objects.all().count())

    def test_post_invalid_file(self):
        c = Container.objects.create()
        b = io.StringIO(u"} not { valid } yaml {{")
        kw = dict(id=str(c.id))
        req = self.post(reverse("container_blueprint", kwargs=kw),
                        data={"file": b}, auth=True, format="multipart")

        resp = ContainerBlueprintView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertIn("detail", resp.data)
        c.refresh_from_db()
        self.assertIsNone(c.blueprint)
        self.assertEqual(0, Blueprint.objects.all().count())

    @mock.patch("cfy_wrapper.tasks.sync_container", return_value=(True, "OK"))
    def test_post_valid_empty_success(self, mock_sync):
        c = Container.objects.create()
        b = io.StringIO(u"valid: yaml")
        kw = dict(id=str(c.id))
        req = self.post(reverse("container_blueprint", kwargs=kw),
                        data={"file": b}, auth=True, format="multipart")

        resp = ContainerBlueprintView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_202_ACCEPTED, resp.status_code)
        mock_sync.assert_called_once()
        self.assertEqual(mock_sync.mock_calls[0][1][0], c)

    @mock.patch("cfy_wrapper.tasks.sync_container", return_value=(False, "NO"))
    def test_post_valid_empty_fail(self, mock_sync):
        c = Container.objects.create()
        b = io.StringIO(u"valid: yaml")
        kw = dict(id=str(c.id))
        req = self.post(reverse("container_blueprint", kwargs=kw),
                        data={"file": b}, auth=True, format="multipart")

        resp = ContainerBlueprintView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_409_CONFLICT, resp.status_code)
        mock_sync.assert_called_once()
        self.assertEqual(mock_sync.mock_calls[0][1][0], c)

    def test_post_no_container(self):
        kw = dict(id="abc")
        b = io.StringIO(u"valid: yaml")
        req = self.post(reverse("container_blueprint", kwargs=kw),
                        data={"file": b}, auth=True)

        resp = ContainerBlueprintView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)
        self.assertIn("detail", resp.data)

    @mock.patch.object(ContainerBlueprintView, "delete",
                       return_value=Response({}))
    def test_delete_route(self, mock_method):
        kw = dict(id="abc")
        url = reverse("container_blueprint", kwargs=kw)
        self.client.delete(url)
        mock_method.assert_called_once()

    def test_delete_invalid_container(self):
        kw = dict(id="abc")
        req = self.delete(reverse("container_blueprint", kwargs=kw), auth=True)

        resp = ContainerBlueprintView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)
        self.assertIn("detail", resp.data)

    def test_delete_busy_container(self):
        b = Blueprint.objects.create()
        c = Container.objects.create(busy=True, blueprint=b)
        kw = dict(id=str(c.id))
        req = self.delete(reverse("container_blueprint", kwargs=kw), auth=True)

        resp = ContainerBlueprintView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_409_CONFLICT, resp.status_code)
        self.assertIn("detail", resp.data)
        c.refresh_from_db()
        self.assertEqual(b, c.blueprint)

    def test_delete_no_blueprint(self):
        c = Container.objects.create()
        kw = dict(id=str(c.id))
        req = self.delete(reverse("container_blueprint", kwargs=kw), auth=True)

        resp = ContainerBlueprintView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertIn("detail", resp.data)

    @mock.patch("cfy_wrapper.tasks.sync_container", return_value=(True, "OK"))
    def test_delete_sync_success(self, mock_sync):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        kw = dict(id=str(c.id))
        req = self.delete(reverse("container_blueprint", kwargs=kw), auth=True)

        resp = ContainerBlueprintView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_202_ACCEPTED, resp.status_code)
        mock_sync.assert_called_once()
        self.assertEqual(mock_sync.mock_calls[0][1][0], c)
        self.assertIsNone(mock_sync.mock_calls[0][1][1])

    @mock.patch("cfy_wrapper.tasks.sync_container", return_value=(False, "NO"))
    def test_delete_sync_fail(self, mock_sync):
        b = Blueprint.objects.create()
        c = Container.objects.create(blueprint=b)
        kw = dict(id=str(c.id))
        req = self.delete(reverse("container_blueprint", kwargs=kw), auth=True)

        resp = ContainerBlueprintView.as_view()(req, **kw)

        self.assertEqual(status.HTTP_409_CONFLICT, resp.status_code)
        mock_sync.assert_called_once()
        self.assertEqual(mock_sync.mock_calls[0][1][0], c)
        self.assertIsNone(mock_sync.mock_calls[0][1][1])


class InputsTest(BaseViewTest):

    def test_not_auth(self):
        req = self.get(reverse("inputs"), auth=False)
        resp = InputsView.as_view()(req)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, resp.status_code)

    @mock.patch.object(InputsView, "get",
                       return_value=Response({}))
    def test_get_route(self, mock_get):
        url = reverse("inputs")
        self.client.get(url)
        mock_get.assert_called_once()

    def test_get(self):
        ins = [Input.objects.create(key=str(n), value="v") for n in range(4)]
        req = self.get(reverse("inputs"), auth=True)

        resp = InputsView.as_view()(req)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.compare(INPUT_FIELDS, resp.data, ins)

    def test_get_render(self):
        ins = [Input.objects.create(key=str(n), value="v") for n in range(4)]
        url = reverse("inputs")

        resp = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        data = json.loads(resp.content)
        self.compare(INPUT_FIELDS, data, ins)

    def test_get_empty(self):
        req = self.get(reverse("inputs"), auth=True)

        resp = InputsView.as_view()(req)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(resp.data, [])

    @mock.patch.object(InputsView, "post",
                       return_value=Response({}))
    def test_post_route(self, mock_get):
        url = reverse("inputs")
        self.client.post(url)
        mock_get.assert_called_once()

    def test_post(self):
        data = [{
            "key": "k1",
            "value": "v1",
            "description": "d1",
        }, {
            "key": "k2",
            "value": "v2",
        }]
        req = self.post(reverse("inputs"), data, auth=True)

        resp = InputsView.as_view()(req)

        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        ins = list(Input.objects.all())
        self.compare(INPUT_FIELDS, resp.data, ins)

    def test_post_render(self):
        data = [{
            "key": "k1",
            "value": "v1",
            "description": "d1",
        }, {
            "key": "k2",
            "value": "v2",
        }]
        url = reverse("inputs")

        resp = self.client.post(url, data=data, format="json")

        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        ins = list(Input.objects.all())
        data = json.loads(resp.content)
        self.compare(INPUT_FIELDS, data, ins)

    def test_post_invalid(self):
        data = [{
            "key": "k1",
            "description": "d1",
        }, {
            "key": "k2",
            "value": "v2",
        }]
        req = self.post(reverse("inputs"), data, auth=True)

        resp = InputsView.as_view()(req)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertEqual(0, Input.objects.all().count())
        self.assertEqual(2, len(resp.data))

    @mock.patch.object(InputsView, "delete",
                       return_value=Response({}))
    def test_delete_route(self, mock_get):
        url = reverse("inputs")
        self.client.delete(url)
        mock_get.assert_called_once()

    def test_delete(self):
        for n in range(4):
            Input.objects.create(key=str(n), value="v")
        req = self.delete(reverse("inputs"), auth=True)

        resp = InputsView.as_view()(req)

        self.assertEqual(status.HTTP_204_NO_CONTENT, resp.status_code)
        self.assertEqual(0, Input.objects.all().count())
