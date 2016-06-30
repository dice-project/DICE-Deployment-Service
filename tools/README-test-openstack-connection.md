OpenStack connection tester
===========================

Introduction
------------

This tool is mainly aimed at developers that can use it to test connection on
various openstack versions.

Usage example
-------------

First thing we need to do is install latest `python-novaclient` Python
package. In order not to break our system, we will use virtualenv for this.

    $ cd /tmp
    $ virtualenv -p python2 venv
    $ . venv/bin/activate
    $ pip install python-novaclient

Now we need to obtain OpenStack RC file. Simply login to your OpenStack
dashboard and follow "Access & Security" -> "API Access". There should be a
couple buttons at the upper-right part of the page that download RC settings.

After we download the settings (we will assume that the RC file has been
downloaded to `/tmp/project-openrc.sh`), we need to source it:

    $ cd /tmp
    $ . project-openrc.sh

When prompted, input password and that should be it. To test if the
environment has been setup properly, run

    $ ./test-openstack-connection.py

If this does not error out, OpenStack installation should be capable of
hosting DICE Deployment Tools along with Cloudify.
