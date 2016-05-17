# DICE deployment service

## About the project

This project contains the DICE deployment service, which provides an abstraction 
of an orchestration tool. The work is a part of the [DICE](http://www.dice-h2020.eu/) 
project results, and is a component of the DICE Deployment Tools suite. More
information about this suite is available in the 
[D5.1 DICE delivery tools - initial version](http://wp.doc.ic.ac.uk/dice-h2020/wp-content/uploads/sites/75/2016/02/D5.1_DICE-delivery-tools-Initial-version.pdf) 
project deliverable.

The DICE deployment service provides a RESTful interface and a simple Web GUI
for managing deployments. It requires a running [Cloudify](http://getcloudify.org/)
manager as a back-end to perform the actual orchestration work.

## Acknowledgement

This project has received funding from the European Union’s [Horizon 2020](http://ec.europa.eu/programmes/horizon2020/) 
research and innovation programme under grant agreement No. 644869.

# Installation

We provide automated installation of the service as a Cloudify TOSCA blueprint
(the recommended installation method), a Vagrant script, and instructions for
manual installation. The instructions assume that you have already deployed
the Cloudify manager in your data centre. Instructions on how to bootstrap 
Cloudify manager are vendor specific and thus depend on where testbed is hosted. 
For detailed documentation on bootstraping a Cloudify manager consult official 
documentation on [installing cloudify][cfy-docs] and 
[boostrapping manager][bootstrap-docs].
 
[cfy-docs]: http://docs.getcloudify.org/3.3.1/intro/installation/
[bootstrap-docs]: http://docs.getcloudify.org/3.3.1/intro/cloudify-manager/

## TOSCA blueprint installation

Currently, we support the following platforms with TOSCA blueprints:

* `fco` - the Flexiant Cloud Orchestrator
* `openstack` - an OpenStack platform

We have tested the blueprints on Ubuntu 14.04 cloud install images, using a
flavour equivalent to 512 MB of RAM, 1 VCPU and 10 GB of storage.

To deploy the blueprint, first make sure you have installed the Cloudify CLI
locally. To install the
Cloudify CLI, [here](http://docs.getcloudify.org/3.3.1/installation/from-script/) 
are the official instructions. Alternatively, we prefer a simple, but direct
approach (but please heed the [prerequisites](http://docs.getcloudify.org/3.3.1/installation/from-script/) 
for your client platform):

```bash
# create a folder for the cloudify CLI, e.g.:
$ mkdir ~/cfy-manager && cd ~/cfy-manager
# initialize the virtual environment
$ virtualenv venv
# activate the virtual environment
$ . venv/bin/activate
# install Cloudify
$ pip install cloudify==3.3.1
```

Next, choose your platform from one of the available ones on the list above, and
prepare the parameters in the respective inputs file. In the `install` subfolder
of the DICE Deployment Service GIT repository you can find templates for the
input files named as `inputs-PLATFORM-example.yaml`. Copy the selected template
to the repository's root directory and fill in the parameters, e.g., for
OpenStack:

```bash
$ cd ~/projects/DICE-deployment-service
$ cp install/inputs-openstack-example.yaml inputs-openstack.yaml
$ nano inputs-openstack.yaml
```

Then, make sure the Cloudify's virtual environment is activated, point the `cfy`
to your Cloudify Manager - the same one that will serve as the DICE Deployment
Service's backend - and use `up.sh` to deploy the blueprint:

```bash
# activate the virtual environment (skip the step if already active from before)
$ . ~/cfy-manager/venv/bin/activate
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
Getting outputs for deployment: dice_deploy2 [manager=10.10.20.115]
 - "http_endpoint":
  *  Description: Web server external endpoint
  *  Value: http://10.10.20.35:8000
```

By default, calling `./up.sh PLATFORM` will create a blueprint and deployment
named `dice_deploy`. It is possible to use a different name by supplying it
as the second (optinal) parameter, e.g.:

```bash
$ ./up.sh openstack staging_deployment
```

There is currently a bug in the deployment process preventing the service to
fully start. As a workaround, the manual steps for starting it are required:

```bash
# Connect to the command line console of the deployment service host
$ ssh ubuntu@10.10.20.35 # ubuntu is the default linux user
# Perform the services start-up
$ ./start.sh
```

Now the service should function properly.

Tearing down the deployment service is then as easy as running `./dw.sh`. By 
default, this script will remove the deployment and blueprint named
`dice_deploy`. It is possible to supply a different name as a parameter, e.g.,
`./dw.sh staging_deployment`.


## Vagrant installation

The goal of the Vagrant installation is currently to set up a working
development deployment as quickly as possible. It sets up
a Django project with some javascript libraries for web GUI.
The service internally uses  Celery that enables the application to run
time-consuming tasks asynchronously i.e., after it has already responded with
HTTP response.

To get started, make sure VirtualBox is installed and then simply execute:
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

```bash
python manage.py runserver 0.0.0.0:8080
```
Now the web GUI is available at `localhost:7080` from your host machine.
Default username is `root` with password `root`. Navigate to `/admin` 
page to add new users. Direct access to REST API is given at `/docs`.
Visualization of your asynchronous tasks is available at `localhost:8055`.

# Using DICE deployment service

## Command line tool

The DICE deplyoment tool comes with a helper utility `dice-deploy-cli` available
in the `tools/` subdirectory. Use it to manually manage the containers and 
deployments. Also use this tool in the automation such as a Continuous
Integration. 

The tool first expects the DICE deployment service URL to be set. This is
possible either through setting the environment variable `DICE_DEPLOY`:

```bash
$ export DICE_DEPLOY=10.10.20.35:8000
```

or by using the action `use`:

```bash
$ ./dice-deploy-cli use http://10.10.20.35:8000
```

This creates a file `.dice-deploy-url` to contain the URL.

Next, we need to authenticate the client with the service. By default, the
installation scripts create a user with user name `root` and password `root`.
We supply these credentials (first user name, then password) to the command
line tool:

```bash
$ ./dice-deploy-cli authenticate root root
```

This call will obtain and store the authentication token in the 
`.dice-deploy-auth` file in the current folder.
All the subsequent calls will use this token to authenticate.

Now we can create a container. This will be a virtual unit in the deployment
tool, which can receive up to one instance of a blueprint. In practice, this 
means that each container will map to up to one blueprint deployment in the
target platform.

A container is identified by a container UUID, but it is helpful (although 
optional) to also assign a short description to a container, making it easier
for humans to understand a container's purpose. We use `create` action:

```bash
$ ./dice-deploy-cli create "Acceptance test environment"
Creating a new container ... DONE.
Container UUID: 02bba363-fb85-4a54-8a2f-f1a11a25ad9d
```

We now have a container known with the UUID `02bba363-fb85-4a54-8a2f-f1a11a25ad9d`.
Let's save it in an environment variable for convenience:

```bash
$ export CONTAINER_UUID="02bba363-fb85-4a54-8a2f-f1a11a25ad9d"
```

We can use it to push a blueprint.

```bash
$ ./dice-deploy-cli deploy $CONTAINER_UUID ../example.tar.gz 
Creating a new deployment ... DONE.
Deployment UUID: b0e1b028-8a8c-408c-b619-206257c20481
```

The command both loads the blueprint in the container and starts the deployment
process. A subsequent call to the same command will have replaced the blueprint,
first uninstalling the existing blueprint and then creating and deploying the
new one.

Again, we will save the obtained deployment UUID in an environment variable:

```bash
$ export DEPLOYMENT_UUID="b0e1b028-8a8c-408c-b619-206257c20481"
```

Deployment process normally takes several minutes, possibly half an hour or 
even more. Considering that the `deploy` action just sends the blueprint to the
service and exits without waiting for the process to finish, we need to be able
to check for the status of the blueprint's deployment in the container. We can
use `status` of the deployment to do that:

```bash
$ ./dice-deploy-cli status $DEPLOYMENT_UUID
Obtaining deployment status ...
uploaded
```

In scripts, it is also useful to be able to wait for the deployment process to
finish before being able to proceed with the deployed application. The CLI
tool provides action `wait-deploy`, which blocks the execution of a script,
internally looping until the deployment either succeeds or finishes with an
error:

```bash
$ ./dice-deploy-cli wait-deploy $CONTAINER_UUID
Current status: pending
Current status: pending
Current status: preparing_deploy
Current status: preparing_deploy
Current status: preparing_deploy
# ...
Current status: working
Current status: working
Current status: working
Current status: working
# ...
```

The following are important final states:

* `deployed` - the final state after the deployment action, indicating success.
* `undeployed` - the final state after the undeployment action, indicating
  success.
* `error` - indicates an error condition, which occurred during the deploying or
  undeploying process.

Once the blueprint deploys, the returned status will be `deployed`. At this 
point we can obtain the deployment's outputs. The outputs
are the values, which depend on the configuration of the blueprint and the
dynamic values such as dynamically assigned addresses or ports. Please note
that the command expects the container's ID, not the inner deployment's:

```bash
$ ./dice-deploy-cli outputs $CONTAINER_UUID | python -mjson.tool
{
  "outputs": {
  * "storm_nimbus_gui": "http://172.16.95.145:8080",
  * "zookeeper_endpoint": "172.16.95.148:2181"
  }
}
```

When we want to free the resources created by the deploy, we can call the tear
down action on the blueprint:

```bash
$ ./dice-deploy-cli teardown $DEPLOYMENT_UUID
Deleting deployment ... DONE.
```

Finally, we can also delete the container.

```bash
$ ./dice-deploy-cli delete $CONTAINER_UUID
Deleting container ... DONE.
```

## Command line tool action reference

Complete reference documentation is displayed when the tool is invoked with no
arguments. To get more in-depth documentation with examples for specific
command, use `./dice-deploy-cli help COMMAND`.

### General actions

* `help`: display help
  * parameters: [command]
  * example: `./dice-deploy-cli help`
  * example: `./dice-deploy-cli help deploy`

* `use`: use the URL as the DICE deployment service URL
  * parameters: url
  * example: `./dice-deploy-cli use http://109.231.122.46:8000`

* `authenticate`: provide username and password to obtain the authentication token
  * parameters: username password
  * example: `./dice-deploy-cli authenticate testuser 123456`

### Container actions

These actions (except for `create`) require the container's UUID as a parameter.

* `create`: creates a new container
  * parameters: description (optional)
  * returns: container-uuid
  * example: `./dice-deploy-cli create`
  * example: `./dice-deploy-cli create "Smart Energy streaming application"`

* `deploy`: creates a new deployment in the container
  * parameters: container-uuid package-file-name
  * returns: deployment-uuid
  * example: `./dice-deploy-cli deploy $CONTAINER_UUID pi-cluster.tar.gz`

* `wait-deploy`: after calling deploy, this will block until deploy finishes
  * parameters: container-uuid
  * example: `./dice-deploy-cli wait-deploy $CONTAINER_UUID`

* `container-info`: reports container state
  * parameters: container-uuid
  * returns: container information
  * example:  `./dice-deploy-cli container-info $CONTAINER_UUID`

* `delete`: deletes an existing container
  * parameters: container-uuid
  * example: `./dice-deploy-cli delete $CONTAINER_UUID`

* `outputs`: get deployment parameters
  * parameters: container-uuid
  * returns: dict of deployment parameters
  * example: `./dice-deploy-cli outputs $CONTAINER_UUID`

* `node-ips`: get a list of node IP host addresses in the container
  * parameters: container-uuid
  * returns: list of dictionaries of node properties
  * example: `./dice-deploy-cli node-ips $CONTAINER_UUID`

* `nodes`: get a list of nodes and their properties in the container
  * parameters: container-uuid [raw]
  * returns: list of dictionaries of node properties
  * example: `./dice-deploy-cli nodes $CONTAINER_UUID`


### Blueprint/deployment actions

These actions require deployment's UUID as a parameter.

* `status`: get deployment status
  * parameters: deployment-uuid
  * returns: the deployment's current status
  * example: `./dice-deploy-cli status $DEPLOYMENT_UUID`

* `teardown`: uninstalls and deletes an existing deployment
  * parameters: deployment-uuid
  * example: `./dice-deploy-cli teardown $DEPLOYMENT_UUID`


### Input actions

Next two actions make it possible to add and delete inputs on deployment
service.

* `input-add`: add an input that is added to all yamls (not archives!)
  * parameters: key value description
  * returns: dict, representing new input
  * example: `./dice-deploy-cli input-add large_flavor_id 654fee342 "flavor"`

* `input-delete`: delete an input
  * parameters: key
  * returns: None
  * example: `./dice-deploy-cli input-delete large_flavor_id`


# Development notes

## Developing with PyCharm
PyCharm supports Vagrant-powered development. You need to set 
project interpreter to point to remote python interpreter at vagrant instance.

## For those who develop in Windows

When developing the shell scripts, make sure the line endings that end up in
deployed file are "\n" i.e. LF and not CRLF. There is a .gitattributes file 
in place that should take care of git side of things on checkout. If you add 
a sensitive file to repository, please update .gitattributes as well.

## Manually resetting and running the services

Move into `dice_deploy_django` folder. There is a `run.sh` script that should
be used to run application.

First, we need to reset application state. Do this by executing:
```bash
$ ./run.sh reset
```

After reseting is done, execute:
```bash
$ ./run.sh
```
to spawn one celery worker and then run development server. 
To stop worker and server, press `ctrl + c` to interrupt django 
development server and script
will take care of celery worker.

For more details about operations, consult `run.sh` source code.

## Web GUI

Dice deployment REST API comes with simple AngularJS web GUI. Source code
resides in `dice_deploy_django/cfy_wrapper_gui/static`. It is a single-page
website with main page served by Django and subpages managed by AngularJS.
Please use bower to install Javascript libraries. Simply run
`bower install` while being in project directory. Gui can be accessed at
http://localhost:7080 if using Vagrant default setup.

### Embedding Web GUI

A simplified version of Web GUI is rendered if you pass container id as a
query parameter. This is particularly useful when rendering container from
Eclipse WebKit plugin. Example url:
```
http://localhost:7080?container-id=f4266342-b46b-46b2-8467-cf317eab5a7a
```


## Managing asynchronous task runner

We use Celery framework for asynchronous command execution. There are upstart 
services used to simplify management of Celery framework. Namely:
 - `sudo service celery-service start|status|stop` - 
   manages worker that consumes messages from main queue
 - `sudo service celery-dashboard start|status|stop` - 
   runs web server on port 5555 where you can see message queue
 - `sudo service celery-test-service start|status|stop` - 
   manages worker that consumes messages from test queue
Vagrant installs these services automatically, but you can do it manually
 by simply copying .conf files from install/upstart-services folder to your
 /etc/init folder. Also make sure that you configure parameters in each
 of the .conf files. Log files can be found in /var/log/upstart folder.
 
 To remove all messages from Celery queues, use Django management command
  `python manage.py celery-service purge`. To run it, you must be in
 dice_deploy_django folder with active virtualenvironment.
 
### Debugging Celery Tasks
To debug asynchronous Celery tasks it is best to use celery-dashboard service.
There you can see all task messages and their statuses. Note that celery-dashboard
service stores all Celery messages into internal database and displays them from there.
It keeps them even after they are dissmissed from the Celery queue. To
clear all messages simply restart celery-dashboard service.

There is also log file (tasks.log) in dice_deploy_django folder where tasks
write to.

### Running tests

In order for tests to run properly, some special settings need to be enabled.
Proper command for executing tests is thus:

    python manage.py test --settings=dice_deploy.settings_tests

For test of specific module, run (example is set to run `test_models` module)

    python manage.py test unit_tests.test_models \
      --settings=dice_deploy.settings_tests
