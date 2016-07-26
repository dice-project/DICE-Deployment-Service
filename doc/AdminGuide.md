# DICE deployment service administration guide

This document describes the steps that an administrator needs to carry out to
set up and maintain the DICE deployment service. The goal of this activity is
to:

* [bootstrap Cloudify Manager](#cloudify-management-installation),
* [deploy the DICE deployment service](#dice-deployment-service-installation),
* [provide configuration to DICE deployment service](#dice-deployment-service-configuration)

## Requirements

* Orchestrator: Cloudify 3.4.0
* Supported platforms:
  * OpenStack Kilo (see [compatibility](http://docs.getcloudify.org/3.3.1/plugins/openstack/#compatibility)
    for Cloudify 3.3.1)
  * Flexiant cloud Orchestrator
* CentOS 7 cloud image for Cloudify
* Ubuntu 14.04 cloud image for DICE deployment service

## Cloudify Management installation

The DICE deployment service relies on an instance of a Cloudify
Manager running in the network. Here are our notes and instructions on
bootstrapping the Cloudify Manager:

* [OpenStack](Cloudify-3.4.0-OpenStack.md)

## DICE Deployment service installation

Cloudify is the back-end of our deployment service with the main purpose of
making deployment of new services as simple as possible. Therefore, the first
service to be deployed with Cloudify should be the DICE deployment service.

As an alternative method of DICE deployment service intstallation, we provide
a Vagant script. However, this method is only usable for experimentaiton and
development of the service, and it still needs a running Cloudify Manager.

### Getting the DICE Deployment service

Regardless of the method, first download the DICE deployment tools using git or
a package download. With git, run the following steps:

```bash
$ mkdir -p ~/dice ; cd ~/dice
$ git clone https://github.com/dice-project/DICE-Deployment-Service.git
$ cd DICE-Deployment-Service
$ git checkout -b v0.2.2 tags/0.2.2
```

Or, to obtain the bundle, use the following steps:

```bash
$ mkdir -p ~/dice ; cd ~/dice
$ wget https://github.com/dice-project/DICE-Deployment-Service/archive/0.2.2.tar.gz
$ tar xzfv 0.2.2.tar.gz
# This step is only to unify the result with the one from the git download
$ mv DICE-Deployment-Service-0.2.2 DICE-Deployment-Service
$ cd DICE-Deployment-Service
```

The package contains a [command line tool](UserGuide.md#command-line-tool),
which we can put in the execution path for convenience:

```bash
$ cd tools
$ export PATH=$PATH:$(pwd)
```

### Installation from TOSCA blueprint

Currently, we support the following platforms with TOSCA blueprints:

* `fco` - the Flexiant Cloud Orchestrator
* `openstack` - an OpenStack platform

We have tested the blueprints on Ubuntu 14.04 cloud install images, using a
flavour equivalent to 512 MB of RAM, 1 VCPU and 10 GB of storage.
To deploy the service, first make sure you have installed the Cloudify CLI
(see [Preparing environment](Cloudify-3.3.1-OpenStack.md#preparing-environment))
locally, and activate the appropriate virtual environment:

```bash
$ cd ~/dice
$ . venv/bin/activate
```

Next, choose your platform from one of the available ones on the list above, and
prepare the parameters in the respective inputs file. In the `install` subfolder
of the DICE Deployment Service GIT repository you can find templates for the
input files named as `inputs-PLATFORM-example.yaml`. Copy the selected template
to the repository's root directory and fill in the parameters, e.g., for
OpenStack:

```bash
$ cd DICE-deployment-service
$ cp install/inputs-openstack-example.yaml inputs-openstack.yaml
$ nano inputs-openstack.yaml
```

Your editor will open with the configuration file, which has all its properties
set to generic values. Follow the comments, which explain the meaning of each
property, replace the generic values with the actual ones, and save the inputs
file.

Then, make sure the Cloudify's virtual environment is activated, point the `cfy`
to your Cloudify Manager - the same one that will serve as the DICE Deployment
Service's backend - and use `up.sh` to deploy the blueprint:

```bash
# activate the virtual environment (skip the step if already active from before)
$ . ~/dice/venv/bin/activate
# configure the Cloudify CLI to use your Cloudify Manager, e.g.
$ cfy use -t 10.10.20.115
# start the deployment
$ ./up.sh openstack
```

The last step will take a while. When it is done, it will print the URL to
the deployment service. If this does not happen because the deployment takes
longer than the preconfigured time, use `cfy` to learn the outputs:

```bash
$ cfy deployments outputs -d dice_deploy
Getting outputs for deployment: dice_deploy [manager=10.10.20.115]
 - "http_endpoint":
  *  Description: Web server external endpoint
  *  Value: http://10.10.20.35:8000
```

Now the RESTful interface is running and the Web interface is available. You can
visit the assigned address (in the above case visit `http://10.10.20.35:8000`)
with your browser. You will be greeted with a prompt for providing credentials:

![DICE deployment service GUI login prompt](images/DICEDeploymentServiceGUILogin.png)

To log in, use the credentials set earlier in the inputs
file, i.e., the values of the `superuser_username` and `superuser_password`).

If additional instances of the service are needed, then we need to name each
deployment differently. By default, calling `./up.sh PLATFORM` will create a 
blueprint and deployment named `dice_deploy`. If we need an instance that is
named differently, we can provide the name as the second parameter of the
`up.sh` tool, e.g.:

```bash
$ ./up.sh openstack staging_deployment
```

Next, proceed to [adding virtual containers](#container-management).

#### Removing the service

Tearing down the deployment service is then as easy as running the `dw.sh` script:

```bash
$ ./dw.sh
```

By default, this script will remove the deployment and blueprint named
`dice_deploy`. It is possible to supply a different name as a parameter, e.g.:


```bash
$ ./dw.sh staging_deployment
```


### Vagrant installation

The goal of the Vagrant installation is currently to set up a working
development deployment as quickly as possible. It sets up
a Django project with some javascript libraries for web GUI.
The service internally uses  Celery that enables the application to run
time-consuming tasks asynchronously i.e., after it has already responded with
HTTP response.

To get started, make sure VirtualBox is installed and then execute:
```bash
$ vagrant up --provider virtualbox
``` 

This creates a new VM is created with everything installed, but the application 
is neither configured nor running yet.

Next, we connect to the VM and configure the endpoint of the Cloudify Manager.

```bash
vagrant ssh
cd dice_deploy_django
nano dice_deploy/local_settings.py
```

Assuming that the Cloudify Manager is located on `172.16.95.115`, the 
`dice_deploy/local_settings.py` should then contain the following line:

```ruby
CFY_MANAGER_URL = "172.16.95.115"
```

Next, we run the web application and the web service from the VM:

    $ ./run.sh

Now the web GUI is available at `localhost:7080` from your host machine.
Default username is `admin` with password `changeme`. Navigate to `/admin`
page to add new users. Direct access to REST API is given at `/docs`.
Visualization of your asynchronous tasks is available at `localhost:8055`.

## DICE deployment service configuration

The TOSCA blueprints can define a list of parameters called
[inputs](http://docs.getcloudify.org/3.3.1/blueprints/spec-inputs/). In DICE
technology librariy, we use the inputs to provide elements related to the
environment or the platform in which the application is being deployed.
Considering that this configuration is relatively static for each instance
of the DICE deployment service, the administrator has to load it only once, but
before the first application can be deployed. The inputs needed therefore depend
on the target platform (OpenStack, FCO, etc.). It is of course possible to
provide additional inputs depending on the needs of the application blueprints.
In the following subsections we provide the minimum inputs list that is common
to all the DICE technology library supported blueprints.

Loading the inputs can be performed by using the
[input actions](UserGuide.md#input-actions) of the
[DICE deployment command line tool](UserGuide.md#command-line-tool-action-reference).
To start with the process, make sure that the tool has been associated with the
DICE deployment service access point, and also properly authenticated:

```bash
$ cd ~/dice
$ dice-deploy-cli use http://10.10.20.35:8000
$ dice-deploy-cli authenticate user pwd434
```

### OpenStack inputs

The OpenStack inputs consist of the following information:

* `agent_user`: defines the name of the Linux user pre-installed and available
  at the VMs provisionned from the cloud image. This user has to be a sudoer,
  configured to run sudo without a password prompt. On Ubunutu 14.04 server,
  that is usually `ubuntu`.
* `{ small | medium | large }_image_id`: the UUID of the VM image to be used
  for provisionning a small, a medium or a large VM instance. All three can
  have the same value.
* `{ small | medium | large }_flavor_id`: the UUID of the image flavour to
  be used when provisionning the VMs. A small instance normally has 512 MB
  of RAM, the medium instance has 1 GB or 2 GB of RAM, a large instance has
  at least 4 GB of RAM.

The UUIDs for images and flavours can be obtained using the `nova` client. See
[this document](Cloudify-3.3.1-OpenStack.md#preparing-inputs) to get
examples of the client usage.

```bash
dice-deploy-cli input-add agent_user "ubuntu" "Agent user"
dice-deploy-cli input-add small_image_id "36dbc4e8-81dd-49f5-9e43-f44a179a64ea" "Small image id"
dice-deploy-cli input-add small_flavor_id "070005dc-9bd5-4c0c-b2c6-88f81a7b7239" "Small flavour id"
dice-deploy-cli input-add medium_image_id "36dbc4e8-81dd-49f5-9e43-f44a179a64ea" "Medium image id"
dice-deploy-cli input-add medium_flavor_id "45170672-5608-473e-af9c-9097510472d6" "Medium flavour id"
dice-deploy-cli input-add large_image_id "36dbc4e8-81dd-49f5-9e43-f44a179a64ea" "Large image id"
dice-deploy-cli input-add large_flavor_id "1bd34fe1-57b3-4937-bf60-5edd35382b78" "Large flavour id"
```

### FCO inputs

For the DICE deployment service installed in the FCO, provide the following
inputs:

* `agent_user`: defines the name of the Linux user pre-installed and available
  at the VMs provisionned from the cloud image. This user has to be a sudoer,
  configured to run sudo without a password prompt. On Ubunutu 14.04 server,
  that is usually `ubuntu`.
* `{ small | medium | large }_image_id`: the UUID of the VM image to be used
  for provisionning a small, a medium or a large VM instance. All three can
  have the same value.
* `{ small | medium | large }_server_type`: the UUID of the image flavour to
  be used when provisionning the VMs. A small instance normally has 512 MB
  of RAM, the medium instance has 1 GB or 2 GB of RAM, a large instance has
  at least 4 GB of RAM.
* `{ small | medium | large }_disk`: the name of the small, medium and large
  storage type as defined in the FCO.
* `username`: User's FCO credentials: the username (e-mail address) or the API
  key user ID. The best practice is to create an API key user in the FCO, which
  is then delegated to the automation. The API key user must be a member of the
  Admin Group to be able to deploy and delete VMs. Obain the API username ID by
  visiting the FCO web GUI console, switching to Users section in the
  navigation at the left side of the interface, clicking on your API Key User
  entry and referring to the API username field. The user id is the first part
  of the entry before the "/" delimiter.
* `password`: user's FCO credentials: the password.
* `customer`: FCO customer ID. For an API key user, this ID is in the part after
  the "/" delimiter of the API username field. For a regular user, obtain this
  ID by visiting th FCO console (the web GUI). In the Users tab, click on one of
  the groups. Then open the Information panel and find the Customer information
  in Related resources & UUIDs.
* `service_url`: the URL to the FCO's API service. For DICE project, this is
  `https://cp.diceproject.flexiant.net`.
* `agent_key`: Set the ID of the SSH key to be used by the agent to make the VM
  accessible. This is the UUID that can be found in the SSH keys section of the
  FCO web GUI console, where you can click on the SSH key designated for
  Cloudify to be able to connect to the VMs, then switch to the Information
  tab. The UUIDs are listed in the Related resources & UUIDs panel for the item
  Network.
* `vdc`: Set the ID of the VCD where the DICE Deployment Service VM will be
  deployed. This is the UUID that can be found in the VCDs section of the FCO
  web GUI console, where you can click on the VCD designated to receive the
  blueprints, then switch to the Information tab. The UUIDs are listed in the
  Related resources & UUIDs panel.
* `network`: Set the ID of the FCO network that the VM will connect to. This is
  the UUID that can be found in the Networks section of the FCO web GUI console,
  where you can click on the network designated to connect the VMs, then switch
  to the Information tab. The UUIDs are listed in the Related resources & UUIDs
  panel for the item Network.

 The following sequence is an example of command line calls to load the
 inputs. Before calling them, replace the values in the example with the
 appropriate ones for your environment:

 ```bash
dice-deploy-cli input-add agent_user ubuntu "Agent user"
dice-deploy-cli input-add small_image_id 87978c6d-5ceb-39b2-8e8b-935503ad0307 "Small image id"
dice-deploy-cli input-add small_server_type "2 GB / 1 CPU" "Small server type"
dice-deploy-cli input-add small_disk "30Gb Storage" "Small disk"
dice-deploy-cli input-add medium_image_id 87978c6d-5ceb-39b2-8e8b-935503ad0307 v
dice-deploy-cli input-add medium_server_type "2 GB / 1 CPU" "Medium server type"
dice-deploy-cli input-add medium_disk "30Gb Storage" "Medium disk"
dice-deploy-cli input-add large_image_id 87978c6d-5ceb-39b2-8e8b-935503ad0307 Large image
dice-deploy-cli input-add large_server_type "2 GB / 1 CPU" "Large server type"
dice-deploy-cli input-add large_disk "30Gb Storage" "Large disk"
dice-deploy-cli input-add username 089e2a3a-5ae9-34e4-b03c-c694268acf1c "FCO username"
dice-deploy-cli input-add password 'p@ssword' "FCO password"
dice-deploy-cli input-add customer e50bfd1b-253a-3290-85ff-95e218398b7e "FCO customer"
dice-deploy-cli input-add service_url "https://cp.diceproject.flexiant.net" "Service URL"
dice-deploy-cli input-add agent_key 288f0541-9921-37a8-a07b-bb47eb27dc10 "Agent key"
dice-deploy-cli input-add vdc 9799fe42-02ef-3929-88d4-c993a02cbe1d "FCO VDC"
dice-deploy-cli input-add network 5264edab-8d29-329d-b4f9-5f8ca17cff78 "FCO network"
```

## Container management

With the Cloudify Manager installed and the DICE deployment service installed
and configured, the users can now start using the service. But to be able to
submit their application deployments, they need to have virtual containers in
place to submit their blueprints to.

To do that in GUI, log in and click on the "**+ New Container**" button
at the top right of the page (marked with an arrow in the picture below). A
prompt will ask for a short description of the new container.
In our example, we named the container "Fraud detection master", imagining that
we are developing a fraud detection application, and this container will be used
by the Continuous Integration to validate the master branch of the development.

![Added a new container](images/DICEDeploymentServiceGUIAddContainer.png)

Each container is identified by a UUID. In the image above, the UUID is circled
in red: `62e8ffa3-4f2c-426e-bcd7-4ce54c572305`. Provide this UUID to the
developers or use it in the CI job.

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


## What is next

This concludes the installation and administration of the DICE deployment
service. The users can now start using it through the web GUI, the command
line interface or completely indirectly through Continuous Integration. The
[user guide](UserGuide.md) provides further instructions.
