# Setting up Cloudify manager on FCO

In this document we will describe specifics of bootstrap procedure for Cloudify
3.4.0 on FCO. The document is based on the
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
    $ pip install cloudify==3.4.0

We can move to the SSH key creation


## Creating SSH key pair

Before we can create new server that will host Cloudify Manager, we need to
prepare SSH key pair that manager will use to connect to other machines.
Execute `ssh-keygen` and follow the instructions. When asked about file, enter
**cfy-manager**. Make sure you create SSH key with no password or thing will
not work!

Now that we have a fresh key, we need to register public key into FCO.
Navigate to FCO's management interface and the click **SSH keys** ->
**create**. Now simply paste public key into proper field and you are done.


## Preparing server

Since flexiant plugin for Cloudify is not sufficiently powerful yet to be
able to bootstrap Cloudify, we need to prepare server manually.

First, make sure that image being used to create new server is CentOS 7 (this
is the only supported OS at the moment).

Also make sure server has enough memory. 4 GB RAM and 4 CPUs is a bare
minimum, but it is much better to go above 6 GB. If this is not possible, use
4 GB and make sure a suitable swap file is also enabled (see below).

During server creation (in bootstrap screens), make sure you add newly
registered key to this server. This is really important and without this key
on the server, bootstrap procedure will fail.

After server is created, start it and make sure you can ssh onto it.

Note that first ssh login can be a bit slow, because by default, `sshd` on
CentOS is configured with `useDNS yes`. In order to remedy that, edit
`/etc/ssh/sshd_conf`, set `useDNS` to `no` and restart `sshd`.


## Preparing inputs

First, we need to obtain official blueprints for manager.

    $ git clone https://github.com/cloudify-cosmo/cloudify-manager-blueprints

Now we need to get proper version of blueprints. Run `cfy --version` and
take note of the version number. Now run `git tag` and find a tag that
matches `cfy` version number and check it out. For example:

    $ cfy --version
    Cloudify CLI 3.4.0
    $ cd cloudify-manager-blueprints
    $ git tag
    3.3.1
    3.4
    $ git checkout -b v3.4.0 tags/3.4
    Switched to a new branch 'v3.4.0'

We need to prepare inputs file now. Open `simple-manager-blueprint-inputs.yaml`
file and fill in the details.  When done, *Provider specific inputs* section
should look something like this:

    public_ip: '109.231.122.110'
    private_ip: '109.231.122.110'
    ssh_user: 'centos'
    ssh_key_filename: 'cfy-manager'
    agents_user: 'ubuntu'

Values of public ip and user can be obtained in Flexiant's control panel. In
the *Security Settings*, we need to enable security by setting the following
keys:

    security_enabled: true
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
the mean time, use longer, ASCII only username and password.

This should give us a reasonable secure installation of Cloudify Manager. Now
we can proceed to actually executing bootstrap procedure.


## Executing bootstrap

Now we need to initialize cfy and setup credentials. We can achive this by running

    $ cfy init
    $ export CLOUDIFY_USERNAME=admin
    $ export CLOUDIFY_PASSWORD=ADMIN_PASS

Now we can start the bootstrap process by executing

    $ cfy bootstrap --install-plugins -p simple-manager-blueprint.yaml \
        -i simple-manager-blueprint-inputs.yaml

Grabbing a cup of coffee and/or going to the restroom is highly recommended at
this step. If everything goes as planned, Cloudify Manager will up and running
in cca. 20 minutes.


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
server's ip address, where we should be greeted by Cloudify's UI.


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


# Official documentation

For further reference, the following links point to the official documentation:

* [How to bootstrap Cloudify Manager v.3.4.0](http://docs.getcloudify.org/3.4.0/manager/bootstrapping/)
