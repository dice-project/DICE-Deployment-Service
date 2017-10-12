#!/usr/bin/env python

import agent_packager.packager as cfyap


URL = "https://github.com/cloudify-cosmo/{}/archive/{}.zip"
AGENT_URL = URL.format("cloudify-agent", "3.4.2")
COMMON_URL = URL.format("cloudify-plugins-common", "3.4.2")
REST_URL = URL.format("cloudify-rest-client", "3.4.2")
SCRIPT_URL = URL.format("cloudify-script-plugin", "1.4")

config = {
    "cloudify_agent_module": AGENT_URL,
    "core_modules": {
        "cloudify_plugins_common": COMMON_URL,
        "cloudify_rest_client": REST_URL,
    },
    "core_plugins": {
        "cloudify_script_plugin": SCRIPT_URL,
    },
}

cfyap.create(config=config)
