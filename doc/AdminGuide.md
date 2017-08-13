# DICE deployment service administration guide

Table of Contents:

1. [Prerequisites](#prerequisites)
    1. [Obtaining infrastructure details](#obtaining-infrastructure-details)
        1. [Amazon EC2](#amazon-ec2)
        1. [OpenStack](#openstack)
        1. [FCO](#fco)
    1. [Cloudify Manager](#cloudify-manager)
1. [Cloudify command line tool installation](#cloudify-command-line-tool-installation)
1. [DICE Deployment service installation](#dice-deployment-service-installation)
    1. [Preparing working environment](#preparing-working-environment)
    1. [Configuring the installation](#configuring-the-installation)
    1. [Running the installation](#running-the-installation)
1. [DICE deployment command line client configuration](#dice-deployment-command-line-client-configuration)
1. [DICE deployment service configuration](#dice-deployment-service-configuration)
    1. [General inputs](#general-inputs)
    1. [Platform inputs](#platform-inputs)
    1. [Monitoring inputs](#monitoring-inputs)
1. [Virtual Deployment Container management](#virtual-deployment-container-management)
1. [Testing installation](#testing-installation)
1. [Monitoring support](#monitoring-support)
1. [Removing the service](#removing-the-service)


## Prerequisites

Installing DICE Deployment Service involves a number of parameters that the
Administrator needs to prepare in advance. Another set of parameters emerges
dynamically during various steps. We recommend to keep the list of parameters
handy at all time. Here is the complete list of the parameters needed (the
variable in parenthesis is the bash environment variable holding the value):

* [Your infrastructure](#obtaining-infrastructure-details) (i.e., OpenStack,
  Amazon EC2, etc.):
  * flavour, instance type or product offer for a small, medium and large VM
  * OS image ID for Ubuntu 14.04
  * OS image ID for CentOS 7
  * Linux username for the two images (`UBUNTU_USERNAME`, `CENTOS_USERNAME`)
  * (FCO only) product offer for a small, medium and large disk
* [Cloudify Manager](#cloudify-manager):
  * IP address (`CFY_ADDRESS`),
  * port (`CFY_PORT`), normally 443 for HTTPS or 80 for HTTP,
  * username and password  (generated in advance for new Cloudify Manager
    installation or that of an existing Cloudify Manager instance -
    `CLOUDIFY_USERNAME`, `CLOUDIFY_PASSWORD`) and
  * path to web service's certificate (`CFY_CERT`).
* DICE Deployment Service:
  * administrator username (chosen in advance)
  * administrator password (chosen in advance)
  * administrator's e-mail address
  * path to the DICE Deployment Service's web service certificate (generated in
    the process)

Apart from Cloudify Manager, we will also need `virtualenv` command installed.
The simplest way of getting this package is to use system's package manager,
since this package is present in almost any distribution of GNU/Linux.

### Obtaining infrastructure details

This is the most tedious part of the process, but it is also fairly
straightforward. We need to collect the relevant information from our
infrastructure. The steps differ depending on the platform, but in all cases
the regular user level account is sufficient.

#### Amazon EC2

* Instance types are available at the [AWS Instance Types] page.
  * The medium sized instance type goes into `AWS_INSTANCE_TYPE` variable for
    Cloudify Manager bootstrap.
* Use [Ubuntu AMI locator] and [CentOS AWS wiki page] to obtain a suitable AMI
  ID for the Ubuntu 14.04 and CentOS 7 images.
* Linux usernames are usually `ubuntu` for Ubuntu and `centos` for CentOS.

[Go back to Prerequisites](#prerequisites)

[AWS Instance Types]: https://aws.amazon.com/ec2/instance-types/

#### OpenStack

The easiest way to obtain what we need is by using the OpenStack's `nova` and
`glance` command line clients. First thing we need to do is install latest
`python-novaclient` and `python-glanceclient` Python package. Open a new
terminal window and run the following commands:

    $ cd /tmp
    $ virtualenv -p python2 venv
    $ . venv/bin/activate
    $ pip install python-novaclient python-glanceclient

Now we need to obtain OpenStack RC file. Simply login to your OpenStack
dashboard and follow "Access & Security" -> "API Access". There should be a
couple buttons at the upper-right part of the page that download RC settings.

After we download the settings (we will assume that the RC file has been
downloaded to `/tmp/project-openrc.sh`), we need to source it:

    $ cd /tmp
    $ . project-openrc.sh

When prompted, input password, and you should be set to use the `nova` command.

To obtain the available flavours, call:

    $ nova flavor-list

You should obtain a table with the available options and note down the
respective values in the `ID` column.

To obtain a list of the available images, call:

    $ glance image-list

In the table displayed by the command should contain entries such as
`centos-7 x86_64` and `ubuntu-14.04 x86_64` in the `Name` column. Note down
their respective values in the `Name` column.

Please note that this output will be specific to your OpenStack installation. If
none of the images contain the needed Ubuntu 14.04 or Centos 7 OS, then please
ask your OpenStack administrator to upload suitable Cloud images.

[Go back to Prerequisites](#prerequisites)

#### FCO

For obtaining the needed parameters, we will use the [FCO web console]. There,
switch to the "Servers" page in the navigation and look for existing servers
in your cluster that independently have the properties that we need: one of the
three suitable compute sizes, one of the three disk sizes, and is either Ubuntu
14.04 or Centos 7. If for any of the size or OS type there is no existing
server, simply create a new temporary one.

Then click on the link with the name of each server to open the server's details
page. Switch to the "Information" tab.

* For Product Offer, note down the value in the "UUID" column of the Product
  offer row.
* For Disk's Product Offer, look for the "Disk" entry in the "Information" tab
  and click the link (either the name or the UUID) of the disk. Then switch to
  "Information" tab and look for the Product offer. Note down the UUID value in
  this row.
* While in the "Information" tab of the disk's details, also look for the row
  with item Image. Check the "Name" value, and if it is one of the Ubuntu 14.04
  or CentOS 7, then note down the "UUID" value.

The following items are only relevant if you are setting up a new instance
of the Cloudify Manager:

* SSH key ID for the ssh key (the Agent key) that the Cloudify Manager will use
  for connecting to orchestrated VMs: switch to "SSH keys" at the top level
  navigation. Look for the key you would like to use (if one does not exist yet,
  see instructions below, then continue here). Click on the selected key to open
  the details page, then switch to the "Information" tab. In the table, look for
  the row with "SSH key" item and note down the value in the "UUID" column.
* Customer UUID: open details of a Server created by the FCO user whose
  credentials will be used by Cloudify. Switch to "Information" tab
  and look for the UUID value in the Customer row.
* VDC: open details of a Server created in the cluster belonging to the target
  VDC. Switch to "Information" tab and look for the UUID value in the VDC row.
* Network UUID: in the same server's "Information" tab, find the server's NIC
  and click on the link. This will open the NIC's detail page. Switch to
  the "Information" tab and look for the "Network" item. Note down the value
  in the UUID column.
* User account UUID: the best practice is to create and assign an API Key
  instead of an actual user to Cloudify. Open the "Users" page at the top level
  navigation. Feel free to click on the "Create API key" and select your new
  user name (which is _not_ what we need for configuring Cloudify) and password.
  Note down the password. Then open the selected user's details and switch to
  the "Information" tab. The username UUID is at the "User" item row's "UUID" column.

To **create a new SSH key**, execute:

    $ mkdir -p ~/cfy-manager && cd ~/cfy-manager
    $ ssh-keygen

and follow the instructions. When asked about file, enter `cfy-agent`. Make sure
you create SSH key with no password, since tools do not support password
protected keys. This will create two files: `cfy-agent` is the private key,
and `cfy-agent.pub` is its public key counterpart.
Now that we have a fresh key, we need to register public key into FCO.  We
must navigate to FCO's management interface and the click "SSH keys" ->
"create". Now we name the key and paste the contents of `cfy-agent.pub` into
proper field. After the key is created, we need to open its detail page and
select "Information" tab on the left and take note of the UUID of the key, since
we will need it later.

[Go back to Prerequisites](#prerequisites)

[FCO web console]: https://cp.diceproject.flexiant.net

### Cloudify Manager

**Existing Cloudify Manager**: in the next steps, we will need the credentials
to access Cloudify Manager `CFY_USERNAME` and `CFY_PASSWORD`. We also need
to obtain the Cloudify Manager's service certificate. This can be an
existing path `CLOUDIFY_SSL_CERT`.

If this certificate is not available, download it directly from the server:

    $ export CLOUDIFY_SSL_CERT=/tmp/cfy.crt
    $ openssl s_client -connect $CFY_ADDRESS:$CFY_PORT < /dev/null 2> /dev/null \
        | openssl x509 -out $CLOUDIFY_SSL_CERT

**New Cloudify Manager installation**: the steps depend on the infrastructure
where we want to install the Cloudify Manager:

* [OpenStack](Cloudify.md)
* [Amazon EC2](Cloudify.md)
* [FCO](Cloudify.md)

## Cloudify command line tool installation

If you arrived here from having just installed Cloudify Manager, you can skip
ahead to [Configuring cfy tool](#configuring-cfy-cli).

The recommended way of installing the DICE Deployment service is by using
Cloudify. This requires that the workstation we are installing from has the
Cloudify's command line tool installed and configured.

We can install cfy tool using the next sequence of commands:

    $ mkdir ~/dds && cd ~/dds
    $ virtualenv venv
    $ . venv/bin/activate
    $ pip install cloudify==3.4.2
    $ pip install -U requests[security]

Build the configuration environment for your Cloudify Manager instance, making
sure to replace `CFY_USERNAME` and `CFY_PASSWORD` with the actual values:

    $ mkdir ~/cfy-manager && cd ~/cfy-manager
    $ cp $CLOUDIFY_SSL_CERT cfy.crt
    $ echo "export CLOUDIFY_USERNAME=CFY_USERNAME" > cloudify.inc.sh
    $ echo "export CLOUDIFY_PASSWORD=CFY_PASSWORD" >> cloudify.inc.sh
    $ echo "export CLOUDIFY_SSL_CERT=$PWD/cfy.crt" >> cloudify.inc.sh

#### Configuring cfy tool

In order to configure the tool we need to execute:

    $ . ~/cfy-manager/cloudify.inc.sh
    $ cd ~/dds
    $ cfy init
    $ cfy use -t CFY_ADDRESS --port CFY_PORT

Make sure you replace `CFY_*` placeholders with Cloudify Manager data. To test
if everything works, execute `cfy status`. This command should output
something similar to this:

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

If everything went well, we are now ready to start service installation.


## DICE Deployment service installation

### Preparing working environment

Previously we have created a `~/dds` folder. We also have a `~/cfy-manager`
folder containing our Cloudify Manager instance's settings and files. Now, we
need to switch to the DICE Deployment Service's project:

    $ cd ~/dds/DICE-Deployment-Service

If this folder does not exist for you yet, obtain it:

    $ cd ~/dds
    $ git clone --depth 1 --branch master \
        https://github.com/dice-project/DICE-Deployment-Service.git
    $ cd DICE-Deployment-Service

We need to make sure that the proper Python virtual environment is activated and
that the Cloudify related environment variables are set:

    $ . ../venv/bin/activate
    $ . ~/cfy-manager/cloudify.inc.sh

Now copy the Cloudify's service certificate into the DICE Deployment Service's
resource folder:

    $ cp $CLOUDIFY_SSL_CERT install/cfy.crt

We have tested the blueprints on Ubuntu 14.04 cloud install images, using a
flavour equivalent to 512 MB of RAM, 1 VCPU and 10 GB of storage.

### Configuring the installation

Next, we must prepare the parameters in the respective inputs file. Copy the
configuration file template for your platform into the working directory and
edit it. E.g., for Amazon EC2, use the the following command:

    $ cp install/aws-dds-config.sh dds-config.sh

For FCO, copy `install/fco-dds-config.sh` and for OpenStack
`install/openstack-dds-config.sh`.

Now open the copy for editing:

    $ $EDITOR dds-config.sh

Carefully examine all the variables and update them with the valid values that
apply to your test bed.

Next, source the configuration by running:

    $ . dds-config.sh

### Running the installation

To start the installation, choose a name for the deployment (or leave the
default name `dice_deploy`) and run the installation script for your platform:

    $ install/install-dds.sh dice_deploy
    Creating deployment inputs for DICE Deployment Service
    Running installation
    install/
    install/fco-config.inc.sh
    install/dds.tar.gz
    install/aws-prepare.sh
    install/fco-prepare.sh
    install/blueprint.yaml
    install/install-dds.sh
    [...]
    Obtaining outputs
    Creating DICE Deployment Service's runtime inputs

    ----------------------------------------------------------------------------
    SUMMARY:
      DICE Deployment Service URL: https://10.50.51.34
      Admin username: admin
      Admin password: 0Ny2VXtEqA7ZD5xZTXFHDBXXheBYtP4F
    ----------------------------------------------------------------------------

The last step will take a while. When it is done, the summary section will
contain the data on the newly created DICE Deployment Service instance. Note
them down, because the URL and the password are dynamic, and the password
cannot be retrieved later.

The script also produces two files:

* `inputs.yaml` - the inputs file for the DICE Deployment Service's blueprint.
  The script has already consumed this file in the process of the service
  installation.
* `dds_inputs.json` - contains the inputs that the DICE Deployment Service should
  supply with each blueprint deployment. We will use this file later.

Now the RESTful interface is running and the Web interface is available. We
can visit the address listed above with our browser and we should be greeted
by a login form. Use the Admin username and password that are also listed above
to log in.

![DICE deployment service GUI login prompt](images/DICEDeploymentServiceGUILogin.png)

Next, we will configure the DICE Deployment Service instance with the inputs
that the service will include with the deployment. We will do that using the
command line client.


## DICE deployment command line client configuration

DICE deployment service is managed and used through RESTful interface calls.
The command line tool `dice-deploy-cli` uses these interfaces
and is available in `tools` subfolder. Complete usage instructions are
available in [user guide](UserGuide.md#command-line-tool-action-reference),
but for the sake of completeness, we will describe the commands that we need
in this document also.

First thing we need to do is obtain server certificate. We can use web browser
for this (export certificate that server identified itself with) or do some
command line magic (`$DDS_ADDRESS` with IP of your instance in the next
command):

    $ openssl s_client -showcerts -connect $DDS_ADDRESS:443 < /dev/null \
        | openssl x509 -out dds.crt

Server certificate has been placed in `dds.crt` file and can be inspected by
executing

    $ openssl x509 -in dds.crt -text -noout

Now that we have server certificate available, we can configure the tool. This
is done by executing the following sequence of commands (replace or set
`$DDS_USERNAME` and `$DDS_PASSWORD` with DICE Deployment Service credentials for
super user, set in inputs file for `superuser_username` and
`superuser_password`, respectively):

    $ tools/dice-deploy-cli cacert dds.crt
    [INFO] - Settings server certificate
    [INFO] - Server certificate set successfully

    $ tools/dice-deploy-cli use https://$DDS_ADDRESS
    [INFO] - Trying to set DICE Deployment Service URL
    [INFO] - Checking DICE Deployment Service URL
    [INFO] - URL set successfully

    $ tools/dice-deploy-cli authenticate $DDS_USERNAME $DDS_PASSWORD
    [INFO] - Checking DICE Deployment Service URL
    [INFO] - Authenticating
    [INFO] - Authorization succeeded

The configuration is stored in the `.dds.conf` file.
If anything went wrong, tool will inform us about the error. To get even more
details, we can also consult log file `.dds.log`. And this concludes tool
configuration. Now we need to set server's inputs.


## DICE deployment service configuration

The TOSCA blueprints can define a list of parameters called
[inputs][cfy-spec-inputs]. In DICE technology library, we use the inputs to
provide elements related to the environment or the platform in which the
application is being deployed. Considering that this configuration is
relatively static for each instance of the DICE deployment service, the
administrator has to load it only once, but before the first application can
be deployed. The inputs needed therefore depend on the target platform
(OpenStack, FCO, etc.).

If you followed the steps of the DICE Deployment Service installation, your
working directory should contain a `dds_inputs.json` file. We upload it by
executing:

    $ tools/dice-deploy-cli set-inputs dds_inputs.json
    [INFO] - Checking DICE Deployment Service URL
    [INFO] - Checking DICE Deployment Service authentication data
    [INFO] - Replacing service inputs
    [INFO] - Successfully updated inputs

Please note that the command replaces any previous values of the inputs in the
`dds_inputs.json` while removing any inputs that are not present in the uploaded
file.

It is of course possible to provide additional inputs
depending on the needs of the application blueprints. In the following
subsections we provide the minimum inputs list that is common to all the DICE
technology library supported blueprints.

And this is it. We successfully configured DICE deployment service that is now
fully operational.


### General inputs

These inputs are not platform specific.

  * `{ ubuntu | centos }_agent_user`: Defines the name of the Linux
    user pre-installed and available on the VMs provisioned from the cloud
    image. This user has to be a sudoer, configured to run sudo without a
    password prompt. The `ubuntu_agent_user` is used on Ubuntu 14.04 servers,
    and there it is usually `ubuntu`, as indicated by default value for this
    input. The `centos_agent_user` will be used on CentOS 7 servers, where the
    value is usually `centos`.
  * `dns_server`: Defines the address of the internal DNS server. This should
    be set to the internal address of the DICE Deployment Service.


### Platform inputs

The platform inputs consist of the following information:

  * `platform`: Name of the platform that is used to deploy blueprints. Valid
    values are `aws`, `fco` and `openstack`.
  * `{ ubuntu | centos }_image_id`: The ID of the VM image to be used for
    provisioning an Ubuntu 14.04 or CentOS 7 VM instance, respectively.
    On OpenStack and FCO platform, this is UUID of the image. On Amazon EC2,
    this is AMI ID - use [Ubuntu AMI locator] and [CentOS AWS wiki page].
  * `{ small | medium | large }_instance_type`: the UUID of the flavour to
    be used when provisioning the VMs. In FCO, this is called a product offer
    ID. A small instance normally has 512 MB of RAM, the medium instance has
    1 GB or 2 GB of RAM, a large instance has at least 4 GB of RAM.
  * `{ small | medium | large }_disk_type`: The name of the small, medium and
    large disk product offers as defined in the FCO. For Amazon and OpenStack
    platforms, these inputs can be set to arbitrary values, since they are
    ignored by the orchestrator.

[Ubuntu AMI locator]: https://cloud-images.ubuntu.com/locator/ec2/
[CentOS AWS wiki page]: https://wiki.centos.org/Cloud/AWS

### Monitoring inputs

DICE TOSCA Library has integrated support for application monitoring. In order
to use monitoring, we must have access to DICE Monitoring server that
applications will report to. Setting up DICE Deployment Service server is out of
scope for this document. Consult
[monitoring tool documentation][dmon-docs] for more information about DICE
Monitoring Service.

When installing Cloudify and DICE Deployment Service, these inputs are present,
but are set to a generic value. Once DICE Deployment Service is set up at a
known internal address, update the following items in the `dds_inputs.json`:

  * `dmon_address`: Main dmon address (eg. 10.50.51.4:5001).
  * `logstash_graphite_address`: Graphite address (eg. 10.50.51.4:5002).
  * `logstash_lumberjack_address`: Lumberjack address (eg. 10.50.51:5003).
  * `logstash_lumberjack_crt`: Lumberjack certificate.
  * `logstash_udp_address`: Logstash udp address (eg. 10.50.51.4:25826).


## Virtual Deployment Container management

With the Cloudify Manager installed and the DICE deployment service installed
and configured, the users can now start using the service. But to be able to
submit their application deployments, they need to have virtual containers in
place to submit their blueprints to.

To do that in GUI, log in and click on the "**+ New Container**" button at the
top right of the page (marked with an arrow in the picture below). A prompt
will ask for a short description of the new container.  In our example, we
named the container "Fraud detection master", imagining that we are developing
a fraud detection application, and this container will be used by the
Continuous Integration to validate the master branch of the development.

![Added a new container](images/DICEDeploymentServiceGUIAddContainer.png)

Each container is identified by a UUID. In the image above, the UUID is
circled in red: `62e8ffa3-4f2c-426e-bcd7-4ce54c572305`. Provide this UUID to
the developers or use it in the CI job.

Using the command line interface, adding a new container can be done with the
following call:

```bash
$ dice-deploy-cli create "Fraud detection master"
DONE.
Container UUID: 75570440-545c-42ed-a677-c54732783e67
```

In this case we receive the UUID of the newly created container in the console.


## Testing installation

In order to make sure everything works as expected, there are a few test
blueprints provided in [examples](../example/) folder that should be uploaded
to some container on freshly installed service.

First blueprint that should be uploaded is
[test-setup.yaml](../example/test-setup.yaml). This blueprint does not use any
external dependencies and creates no physical nodes (virtual machines, etc.).
This makes it perfect for testing if all of the pieces are properly wired
together. If the test succeeds, container in UI should look something like the
screenshot below.

![Deployed test blueprint](images/dice-deployment-service-tester.png)

Second blueprint that should be uploaded is one of the
`test-server-<platform>.yaml`, depending on the platform where service is
installed. This blueprint will create a single virtual machine and install
demo web server that serves static file onto it.

![deployed server test](images/dice-deployment-service-server-tester.png)

If all of the tests finished, deployment service is set up correctly and ready
for real work.


## Monitoring support

We have already seen that there are some inputs that control monitoring
support. But this is only the first half of the monitoring story, since
setting the appropriate inputs only saves the configuration of the monitoring
service for any blueprints that require monitored nodes. To actually monitor
application being deployed, we must enable this explicitly in blueprint.
Consult [example blueprint with monitoring enabled][blue-monitored] for more
information.


[cfy-spec-inputs]: http://docs.getcloudify.org/3.4.0/blueprints/spec-inputs/
[Prerequisites-wiki]: https://github.com/dice-project/DICE-Deployment-Service/wiki/Prerequisites
[Installation-wiki]: https://github.com/dice-project/DICE-Deployment-Service/wiki/Installation
[Getting-Started-wiki]: https://github.com/dice-project/DICE-Deployment-Service/wiki/Getting-Started
[Links-and-References-wiki]: https://github.com/dice-project/DICE-Deployment-Service/wiki/Links-and-References
[Changelog-wiki]: https://github.com/dice-project/DICE-Deployment-Service/wiki/Changelog
[dmon-docs]: https://github.com/dice-project/DICE-Knowledge-Repository/wiki/DICE-Knowledge-Repository#monitoring
[blue-monitored]: https://github.com/dice-project/DICE-Deployment-Examples/blob/master/storm/storm-openstack-monitored.yaml


## Removing the service

Tearing down the deployment service is then as easy as running the `dw.sh`
script and providing the name of the deployment as the parameter:

    $ ./dw.sh dice_deploy
