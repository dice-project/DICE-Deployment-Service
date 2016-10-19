# Setting up Cloudify manager on OpenStack

In this document we will describe specifics of bootstrap procedure for Cloudify
3.4.0 on OpenStack. The document is based on the
[official instructions](#official-documentation), but since we patched the
official packages a bit in order to support wider variety of OpenStack
installations, instructions are also a bit modified.


## Preparing environment

First we need to install prerequisites for Cloudify's CLI client. For
Redhat related GNU/Linux distributions, following packages need to be
installed: `python-virtualenv` and `python-devel`. Adjust properly for
Ubuntu and the like.

Now create new folder, create new python virtual environment and install
`cloudify` package.

    $ mkdir -p ~/dice && cd ~/dice
    $ virtualenv venv
    $ . venv/bin/activate
    $ pip install cloudify==3.4.0

We can move to the bootstrap procedure now.


## Preparing inputs

First, we need to obtain official blueprints for manager.

    $ git clone --depth 1 --branch feature/keystoneauth \
        https://github.com/dice-project/cloudify-manager-blueprints.git
    $ cd cloudify-manager-blueprints

Next, we need to install dependencies that are required by manager blueprint.
We do this by executing

    $ cfy init
    $ cfy local install-plugins -p openstack-manager-blueprint.yaml

Now we need to get our OpenStack credentials. Navigate to your OpenStack
dashboard and click "Access & security", "API Access" and then download
OpenStack RC file. We will assume here that the file has been downloaded to
`~/dice/os-rc.sh`. Next, we need to source this file by running

    $ . ~/dice/os-rc.sh

After this is done, we can run a special helper script that serves two
purposes:

 1. It tests whether python clients support our OpenStack installation and
 2. it makes it a breeze to prepare inputs.

Usage is really simple. Just execute

    $ ./create-openstack-inputs.py > os-inputs.yaml

and follow the instructions. Just make sure you use CentOS image when asked
about image and make sure that flavor that you use has at least 4 GB of RAM
and at least 2 CPUs. Another thing that can cause troubles down the road are
non-unique names of various resources. This is problematic only if you have
multiple cloudify installations being hosted on the same OpenStack
installation. The input preparation script asks about prefix that can be used
to avoid name collisions. Default prefix is set ot `cfy-`, but you can chnage
it to just about anything.

When the script terminates, `os-inputs.yaml` file will contain data that can
be used to bootstrap manager.

In order to fortify installation, we will add simple credentials to Cloudify
manager. This is achieved by adding the following lines to `os-inputs.yaml`
file:

    security_enabled: true
    admin_username: admin
    admin_password: ADMIN_PASS
    rabbitmq_username: cloudify
    rabbitmq_password: RABBIT_PASS

Replace `ADMIN_PASS` and `RABBIT_PASS` placeholders with secure passwords.
**WARNING:** Current version of Cloudify agent that gets installed on manager
has a bug that prevents connecting to RabbitMQ if `rabbitmq_username`or
`rabbitmq_password` contains characters that need to be escaped when used in
URLs. Bug has been fixed, but current version does not have it applied yet. In
the mean time, use longer, ASCII only username and password.

Now we can proceed to actually executing bootstrap procedure.


## Executing bootstrap

First, we need to create initial folder structure for bootstrap process.
Running `cfy init` will take care of that. After this is done, we can
finally bootstrap the manager by executing

    $ export CLOUDIFY_USERNAME=admin
    $ export CLOUDIFY_PASSWORD=ADMIN_PASS
    $ cfy bootstrap -p openstack-manager-blueprint.yaml -i os-inputs.yaml
    $ cfy status


## Removing installation

Simply execute `cfy teardown -f`. This will remove all traces of cloudify
manager from openstack.

# Official documentation

For further reference, the following links point to the official documentation:

* [How to bootstrap Cloudify Manager v.3.4.0](http://docs.getcloudify.org/3.4.0/manager/bootstrapping/)
* [OpenStack bootstrap reference v.3.4.0](http://docs.getcloudify.org/3.4.0/manager/bootstrap-reference-openstack/
