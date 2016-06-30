#!/usr/bin/env python2

from __future__ import print_function

from keystoneauth1 import loading, session
from novaclient import client

import sys
import os


ENV_PREFIX = "OS_"
VALID_AUTH_VARS = {
    "OS_AUTH_URL", "OS_PASSWORD", "OS_USERNAME", "OS_USER_ID",
    "OS_USER_DOMAIN_ID", "OS_USER_DOMAIN_NAME", "OS_TRUST_ID", "OS_DOMAIN_ID",
    "OS_DOMAIN_NAME", "OS_PROJECT_ID", "OS_PROJECT_NAME", "OS_TENANT_ID",
    "OS_TENANT_NAME", "OS_PROJECT_DOMAIN_ID", "OS_PROJECT_DOMAIN_NAME",
}


def execute_test(auth_args, misc_args):
    loader = loading.get_plugin_loader("password")
    auth = loader.load_from_options(**auth_args)
    sess = session.Session(auth=auth)
    nova = client.Client("2", session=sess, **misc_args)
    nova.flavors.list()


def get_options():
    def gen_pair(name):
        return {name.lstrip(ENV_PREFIX).lower(): os.environ[name]}

    misc_opts = {}
    auth_opts = {}
    for var in os.environ:
        if var.startswith(ENV_PREFIX):
            if var in VALID_AUTH_VARS:
                auth_opts[var.lstrip(ENV_PREFIX).lower()] = os.environ[var]
            else:
                misc_opts[var.lstrip(ENV_PREFIX).lower()] = os.environ[var]

    return auth_opts, misc_opts, 3 if "project_name" in auth_opts else 2


if __name__ == "__main__":
    auth, misc, version = get_options()
    if auth.get("auth_url", None) is None:
        print("Source OpenStack rc file before running this test.")
        print("You can obtain rc file from OpenStack dashboard.")
        print("Navigate to 'Access & Security' -> 'API Access' and click")
        print("'Download OpenStack RC File'. If there are multiple download")
        print("options, select proper version (admin is your friend here).")
        sys.exit(0)

    print("It seems that you wish to use identity version {}.".format(version))
    print("Running auth test ...")
    execute_test(auth, misc)
    print("Things look great!;) Thank you for your time.")
