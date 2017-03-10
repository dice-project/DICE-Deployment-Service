# Setting up Cloudify manager on FCO

In this document we will describe specifics of bootstrap procedure for Cloudify
3.4.1 on FCO. The document is based on the
[official instructions](#official-documentation).


## Preparing environment

First we need to install prerequisites for Cloudify's CLI client. For
Red Hat related GNU/Linux distributions, following packages need to be
installed: `python-virtualenv` and `python-devel`. Adjust properly for
Ubuntu and the gang.

Now create new folder, create new python virtual environment and install
`cloudify` package.

    $ mkdir ~/cfy-manager && cd ~/cfy-manager
    $ virtualenv venv
    $ . venv/bin/activate
    $ pip install cloudify==3.4.1

Next, we need to obtain official blueprints for manager and checkout the
**3.4.1** tag:

    $ git clone https://github.com/cloudify-cosmo/cloudify-manager-blueprints
    $ cd cloudify-manager-blueprints
    $ git checkout -b v3.4.1 tags/3.4.1

With blueprints present locally, we can install dependencies that are required
by manager blueprint. We do this by executing

    $ cfy init
    $ cfy local install-plugins -p simple-manager-blueprint.yaml

In order to prevent `requests` experiencing a fit when confronted with some
certificates, we reinstall them using `security` flag:

    $ pip install -U requests[security]

We can move to the SSH key creation now.


## Creating SSH key pair

Before we can create new server that will host Cloudify Manager, we need to
prepare SSH key pair that manager will use to connect to other machines.
Execute `ssh-keygen` and follow the instructions. When asked about file, enter
**cfy-manager**. Make sure you create SSH key with no password, since
tools do not support password protected keys.

Now that we have a fresh key, we need to register public key into FCO.  We
must navigate to FCO's management interface and the click **SSH keys** ->
**create**. Now we name the key and paste public key into proper field. After
the key is created, we need to open its detail page and select **Information**
tab on the left and take note of the UUID of the key, since we will need it
later.


## Preparing server

Since FCO plugin for Cloudify is not sufficiently powerful yet to be able to
bootstrap Cloudify, we need to prepare server manually.

First, we must make sure that image being used to create new server is CentOS
7 (this is the only supported OS at the moment) and that server has enough
memory. 4 GB RAM and 4 CPUs is a bare minimum, but it is much better to go
above 6 GB. If this is not possible, we can still use 4 GB with suitable swap
file enabled (see below).

When we are creating new server using FCO's interface, we must add newly
registered key to this server in bootstrap screens. This is really important
and without this key on the server, bootstrap procedure will fail.

After server is created, we must start it and make sure we can ssh onto it
using the key we created earlier. To test this, execute `ssh -i cfy-manager
centos@IP`, where `IP` should be replaced by server's IP address.

Note that first ssh login can be a bit slow, because by default, `sshd` on
CentOS is configured with `useDNS yes`. In order to remedy that, we can edit
`/etc/ssh/sshd_conf`, set `useDNS` to `no` and restart `sshd` with `sudo
systemctl restart sshd`.


## Preparing inputs


We need to prepare inputs file now. Open `simple-manager-blueprint-inputs.yaml`
file and fill in the details.  When done, *Provider specific inputs* section
should look something like this:

    public_ip: '109.231.122.110'
    private_ip: '109.231.122.110'
    ssh_user: 'centos'
    ssh_key_filename: 'cfy-manager'
    agents_user: 'ubuntu'

Values of public IP and user can be obtained in Flexiant's control panel. In
the *Security Settings*, we need to enable security by setting the following
keys:

    security_enabled: true
    ssl_enabled: true
    admin_username: admin
    admin_password: ADMIN_PASS

Select username and password sensibly. Last section that we need to modify is
*RabbitMQ Configuration*. Set username and password for RabbitMQ broker.

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
validations, since they will fail. We can do that by searching for "Bootstrap
Validations" section and set `ignore_bootstrap_validations` to `true`.

This should give us a reasonable secure installation of Cloudify Manager. Now
we can proceed to creating server certificate.


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
    $ cfy bootstrap -p simple-manager-blueprint.yaml \
        -i simple-manager-blueprint-inputs.yaml

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
