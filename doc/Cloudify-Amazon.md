# Setting up Cloudify manager on Amazon EC2

In this document we will describe specifics of bootstrap procedure for Cloudify
3.4.1 on Amazon. The document is based on the
[official instructions](#official-documentation).


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
    $ cfy local install-plugins -p aws-ec2-manager-blueprint.yaml

Now we need to get our Amazon credentials. Navigate to your
[AWS IAM console](https://console.aws.amazon.com/iam/) and create new user
with programmatic access. Make sure this user can use EC2 services. You can
use policy similar to the one shown below:

    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Sid": "Stmt1488457587000",
          "Effect": "Allow",
          "Action": [ "ec2:*" ],
          "Resource": [ "*" ]
        }
      ]
    }

After new user is created, write down both access keys that are shown.

To test new credentials, we will install CLI client and take it for a test
run. Installation is as simple as executing:

    $ pip install awscli

After installation finished, we have `aws` command available to us. To
configure he client, we need to run `aws configure` and answer questions.
After the client is configured, execute:

    $ aws ec2 describe-vpcs
    {
      "Vpcs": [
        {
          "VpcId": "vpc-f2952897",
          "InstanceTenancy": "default",
          "State": "available",
          "DhcpOptionsId": "dopt-480dec2d",
          "CidrBlock": "172.30.0.0/16",
          "IsDefault": true
        }
      ]
    }

If the result looks roughly the same as the listing above, credentials work OK
and we can proceed.

In order to prevent `requests` experiencing a fit when confronted with some
certificates, we reinstall them using `security` flag:

    $ pip install -U requests[security]

That last command completes our environment setup. Now we must prepare
inputs that will be used by bootstrap process.


## Preparing inputs

We need to prepare inputs file now. Open `aws-ec2-manager-blueprint-inputs.yaml`
file and fill in the details.  When done, *Provider specific inputs* section
should look something like this:

    aws_access_key_id: AKIAIKJHDFKDZU56KJDF
    aws_secret_access_key: AnPFfAjdhkKJnfkjskuZ56JKjndfkKJLH7643klLKBJGhbd
    image_id: ami-0f80e87c
    instance_type: m3.medium
    ssh_key_filename: /home/tadej/cloudify-manager-kp.pem
    agent_private_key_path: /home/tadej/cloudify-agent-kp.pem
    ssh_user: ec2-user
    ec2_region_name: eu-west-1
    ec2_vpc_cidr: 10.50.51.0/24
    manager_elastic_ip: <replaced later>

In the *Security Settings*, we need to enable security by setting the
following keys:

    security_enabled: true
    ssl_enabled: true
    admin_username: cfy_admin
    admin_password: Dlskdjfiurjhelkjash475ksdsd7#5

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


## Creating elastic IP for manager

Since our goal is to access Cloudify Manager over https, we need to create
elastic IP address beforehand. This way we will be able to generate server
key and certificate that we will pass to bootstrap procedure.

Creating elastic IP can be done via AWS console, but in this guide, we will
create elastic IP using command line tools that we installed earlier.

    $ aws ec2 allocate-address --domain vpc
    {
      "PublicIp": "34.252.51.224",
      "Domain": "vpc",
      "AllocationId": "eipalloc-5121c936"
    }

To make manager actually use this floating IP, we need to replace the
placeholder input from the previous section with the actual elastic IP.

    manager_elastic_ip: 34.252.51.224

Now we need to create server key and certificate.


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

    $ export CLOUDIFY_USERNAME=cfy_admin
    $ export CLOUDIFY_PASSWORD=ADMIN_PASS
    $ export CLOUDIFY_SSL_CERT="$PWD/resources/ssl/server.crt"
    $ cfy bootstrap -p aws-ec2-manager-blueprint.yaml \
        -i aws-ec2-manager-blueprint-inputs.yaml

Note that installation step may take up to 30 minutes on a slow platform, but
in most cases, it should finish in no more than 15 minutes.


## Testing installation

First thing we can do is execute `cfy status`. Output of that command should
be similar to this:

    Getting management services status... [ip=34.252.51.224]
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

To perform initial removal of manager components, we must execute
`cfy teardown -f`. This will probably leave manager's volume still present in
AWS, because for some reason, volume attached to manager instance has
`DeleteOnTermination` set to `false`. We can safely remove this volume in
order to avoid being billed for something that we do not use or need.


# Official documentation

For further reference, the following links point to the official documentation:

* [How to bootstrap Cloudify Manager](http://docs.getcloudify.org/3.4.1/manager/bootstrapping/)
* [AWS bootstrap reference](http://docs.getcloudify.org/3.4.1/manager/bootstrap-ref-aws/)
