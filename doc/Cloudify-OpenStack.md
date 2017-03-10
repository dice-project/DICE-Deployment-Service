# Setting up Cloudify manager on OpenStack

In this document we will describe specifics of bootstrap procedure for Cloudify
3.4.1 on OpenStack. The document is based on the
[official instructions](#official-documentation), updated with instructions
on how to use latest OpenStack plugin to bootstrap it.


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
    $ pip install cloudify==3.4.1

This being out of the way, we can now install required python packages.
But first, we need to obtain official blueprints for manager.

    $ git clone --depth 1 --branch feature/ssl \
        https://github.com/xlab-si/cloudify-manager-blueprints.git
    $ cd cloudify-manager-blueprints

With blueprints present locally, we can install dependencies that are required
by manager blueprint. We do this by executing

    $ cfy init
    $ cfy local install-plugins -p openstack-manager-blueprint.yaml

Now we need to get our OpenStack credentials. Navigate to your OpenStack
dashboard and click "Access & security", "API Access" and then download
OpenStack RC file. We will assume here that the file has been downloaded to
`~/dice/os-rc.sh`. Next, we need to source this file by running

    $ . ~/dice/os-rc.sh

In order to prevent `requests` experiencing a fit when confronted with some
certificates, we reinstall them using `security` flag:

    $ pip install -U requests[security]

That last command completes our environment setup. Now we must prepare
inputs that will be used by bootstrap process.


## Preparing inputs

Checked out repository contains a special helper script that serves two
purposes:

 1. It tests whether python clients support our OpenStack installation and
 2. it makes it a breeze to prepare inputs.

Usage is really simple. Just execute

    $ ./create-openstack-inputs.py > os-inputs.yaml

and follow the instructions. Just make sure you use CentOS image when asked
about image and make sure that flavor that you use has at least 6 GB of RAM
and at least 4 CPUs. It is possible to install Cloudify Manager to server
with only 4 GB of RAM, but in this case, validations need to be disabled and
swap activated as described below.

Another thing that can cause troubles down the road are non-unique names of
various resources. This is problematic only if you have multiple cloudify
installations being hosted on the same OpenStack installation. The input
preparation script asks about prefix that can be used to avoid name
collisions. Default prefix is set to `cfy-`, but you can change it to just
about anything.

When the script terminates, `os-inputs.yaml` file will contain data that can
be used to bootstrap manager.

In order to fortify installation, we will set some security inputs for
Cloudify manager. This is achieved by adding the following lines to
`os-inputs.yaml` file:

    security_enabled: true
    ssl_enabled: true
    admin_username: admin
    admin_password: ADMIN_PASS
    rabbitmq_username: cloudify
    rabbitmq_password: RABBIT_PASS

Replace `ADMIN_PASS` and `RABBIT_PASS` placeholders with secure passwords.
**WARNING:** Current version of Cloudify agent that gets installed on manager
has a bug that prevents connecting to RabbitMQ if `rabbitmq_username`or
`rabbitmq_password` contains characters that need to be escaped when used in
URLs. Bug has been fixed, but current version does not have it applied yet. In
the mean time, use longer username and password that match regular expression
`[A-Za-z0-9_.~-]+`.

If our server has less than 6 GB of RAM, we should also disable bootstrap
validations, since they will fail. We can do that by appending the following
line to our inputs:

    ignore_bootstrap_validations: true

Next, we must create floating IP for the server.


## Creating floating IP for manager

Since our goal is to access Cloudify Manager over https, we need to create
floating IP address beforehand. This way we will be able to generate server
key and certificate that we will pass to bootstrap procedure.

Creating floating IP can be done via OpenStack web interface, but its id still
needs to be retrieved using command line tools. In this guide, we will create
floating IP using neutron.

    $ neutron floatingip-create NETWORK
    Created a new floatingip:
    +---------------------+--------------------------------------+
    | Field               | Value                                |
    +---------------------+--------------------------------------+
    | description         |                                      |
    | dns_domain          |                                      |
    | dns_name            |                                      |
    | fixed_ip_address    |                                      |
    | floating_ip_address | 10.10.43.132                         |
    | floating_network_id | 753940e0-c2a7-4c9d-992e-4d5bd71f85aa |
    | id                  | e2f2955f-cdd8-4cd7-a73a-ade4c79a6a69 |
    | port_id             |                                      |
    | router_id           |                                      |
    | status              | DOWN                                 |
    | tenant_id           | b478d718d45d4831a2a85f48cdfa1899     |
    +---------------------+--------------------------------------+

Replace `NETWORK` in the command above with the name of the network you
selected when creating inputs. To make manager actually use this floating IP,
we need to append the following line to the inputs:

    manager_floating_ip_id: e2f2955f-cdd8-4cd7-a73a-ade4c79a6a69

Replace `id` in the example above appropriately. Now we need to create server
key and certificate.


## Creating server certificate

Instructions on how to create server certificate are out of scope for this
document. If you need help with this, consult
[certificate instructions](certificates.md#creating-self-signed-certificates).

After certificate is ready, place it (along with generated key) into
`resources/ssl` folder and change their names to `server.crt` and `server.key`
respectively. Now we can proceed to actually executing bootstrap procedure.


## Executing bootstrap

Since we enabled security options in blueprint, we need to export some
environment variables that will inform cfy command about various settings that
we used. After this is done, we can bootstrap the manager. Commands that
perform all described actions are:

    $ export CLOUDIFY_USERNAME=admin
    $ export CLOUDIFY_PASSWORD=ADMIN_PASS
    $ export CLOUDIFY_SSL_CERT="$PWD/resources/ssl/server.crt"
    $ cfy bootstrap -p openstack-manager-blueprint.yaml -i os-inputs.yaml

Note that installation step may take up to 30 minutes on a slow platform,
but in most cases, it should finish in no more than 15 minutes.


## Testing installation

First thing we can do is execute `cfy status`. Output of that command should
be similar to this:

    Getting management services status... [ip=109.231.122.46]
    Services:
    +--------------------------------+---------+
    |            service             |  status |
    +--------------------------------+---------+
    | InfluxDB                       | running |
    | Celery Management              | running |
    | Logstash                       | running |
    | RabbitMQ                       | running |
    | AMQP InfluxDB                  | running |
    | Manager Rest-Service           | running |
    | Cloudify UI                    | running |
    | Webserver                      | running |
    | Riemann                        | running |
    | Elasticsearch                  | running |
    +--------------------------------+---------+

Another way to test if manager is working is to point our web browser to
server's IP address, where we should be greeted by Cloudify's UI.


## Enabling swap

To use a swap file, either use an image, which enables this by default,
or create one manually. To do that, first create a file with at least
6 GB to serve as a swap file. Notice that `fallocate` will not produce
a usable swap file on the Centos's default file system.

    $ sudo su
    $ dd if=/dev/zero of=/swapfile bs=1MB count=6144

    $ chmod 0600 swapfile
    $ mkswap /swapfile
    $ swapon /swapfile

Then add the following line to the `/etc/fstab` to make the change
permanent:

    /swapfile	none	swap	defaults	0	0


## Granting access to the Cloudify Manager

In order for our users to be able to use installed manager, we need to give
them next pieces of information:

 1. manager's IP address (address of the server we created),
 2. manager's port (443),
 3. manager's username and password (*admin* and *ADMN_PASS* in our case) and
 4. manager's certificate (*resources/ssl/server.crt*).

Users can now access manager by installing Cloudify command-line tool (`cfy`)
and executing:

    $ cfy init
    $ export CLOUDIFY_USERNAME=admin
    $ export CLOUDIFY_PASSWORD=ADMIN_PASS
    $ export CLOUDIFY_SSL_CERT="/path/to/server.crt"
    $ cfy use -t manager_ip_address --port 443


## Removing installation

Simply execute `cfy teardown -f`. This will remove all traces of Cloudify
manager from OpenStack.


# Official documentation

For further reference, the following links point to the official documentation:

* [How to bootstrap Cloudify Manager v.3.4.1](http://docs.getcloudify.org/3.4.1/manager/bootstrapping/)
* [OpenStack bootstrap reference v.3.4.1](http://docs.getcloudify.org/3.4.1/manager/bootstrap-reference-openstack/)
