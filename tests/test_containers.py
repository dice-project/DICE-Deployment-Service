from base import BaseTest


class ContainerTest(BaseTest):

    def test_container_create_destroy(self):
        desc = self.get_unique_str("container")

        resp = self.post("containers", True, json=dict(description=desc))

        self.assertEqual(201, resp.status_code)
        data = resp.json()
        self.assertEqual(data["description"], desc)
        self.assertIsNone(data["blueprint"])
        self.assertIn("id", data)
        self.assertIn("modified_date", data)

        url = "containers/{}".format(data["id"])

        resp = self.delete(url, True)
        self.assertEqual(204, resp.status_code)

        resp = self.get(url, True)
        self.assertEqual(404, resp.status_code)

    def test_container_prevent_create_no_auth(self):
        desc = self.get_unique_str("container")

        resp = self.post("containers", False, json=dict(description=desc))

        self.assertEqual(401, resp.status_code)
