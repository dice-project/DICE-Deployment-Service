from base import BaseTest

import time


class BlueprintTest(BaseTest):

    TERMINAL_STATES = {"deployed", "present"}

    def test_valid_blueprint_deploy_undeploy(self):
        blueprint = self.get_blueprint("test-setup.yaml")
        desc = self.get_unique_str("container")

        resp = self.post("containers", True, json=dict(description=desc))

        data = resp.json()
        container_url = "containers/{}".format(data["id"])
        blueprint_url = "{}/blueprint".format(container_url)

        with open(blueprint, "rb") as f:
            resp = self.post(blueprint_url, True, files=dict(file=f))

        self.assertEqual(202, resp.status_code)
        self.add_blueprint_to_cleanup(resp.json()["id"])

        # Wait for blueprint to get from queue
        for _ in range(10):
            time.sleep(3)
            resp = self.get(blueprint_url, True)
            if resp.status_code != 200:
                continue
            if resp.json()["state_name"] == "present":
                continue
            if resp.json()["state_name"] in self.TERMINAL_STATES:
                break
            if resp.json()["in_error"]:
                break

        data = self.get(blueprint_url, True).json()
        self.assertTrue(data["in_error"],
            "Error condition in state {}".format(data["state_name"]))
        self.assertEqual(data["state_name"], "deployed")
        # TODO: check for proper outputs

        resp = self.delete(blueprint_url, True)

        self.assertEqual(202, resp.status_code)

        for _ in range(10):
            time.sleep(3)
            resp = self.get(blueprint_url, True)
            if resp.status_code == 400:
                break

        resp = self.get(blueprint_url, True)
        self.assertEqual(400, resp.status_code)

        resp = self.delete(container_url, True)
        self.assertEqual(204, resp.status_code)

    def test_invalid_blueprint(self):
        blueprint = self.get_blueprint("test-invalid-blueprint.yaml")
        desc = self.get_unique_str("container")

        resp = self.post("containers", True, json=dict(description=desc))

        data = resp.json()
        container_url = "containers/{}".format(data["id"])
        blueprint_url = "{}/blueprint".format(container_url)

        with open(blueprint, "rb") as f:
            resp = self.post(blueprint_url, True, files=dict(file=f))

        self.assertEqual(202, resp.status_code)
        self.add_blueprint_to_cleanup(resp.json()["id"])

        # Wait for blueprint to get from queue
        for _ in range(10):
            time.sleep(3)
            resp = self.get(blueprint_url, True)
            if resp.status_code != 200:
                continue
            if resp.json()["in_error"]:
                break

        data = self.get(blueprint_url, True).json()
        self.assertEqual(data["state_name"], "uploading_to_cloudify")
