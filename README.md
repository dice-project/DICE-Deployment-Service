# DICE deployment tool

Simple wrapper around Cloudify orchestration tool.
Provides both REST API and web GUI for it.


## Important general information

When developing the shell scripts, make sure the line endings that end up in
deployed file are "\n" i.e. LF and not CRLF. There is a .gitattributes file 
in place that should take care of git side of things on checkout. If you add 
a sensitive file to repository, please update .gitattributes as well.


## Developer Setup

### What do I need to install?
As a developer you need to prepare environment for Wrapper, which is nothing
but a Django project with some javascript libraries for web GUI.
Besides, you need to setup and run powerfull Django addon, Celery, that
enables Django to run time-consuming tasks asynchronously i.e. after it
has already responded with HTTP response.

### How do I install it?
In order to minimize the effort of getting development environment up
and running, vagrant file, along with simple provisioning scripts is
provided. To get started, make sure VirtualBox is installed and then 
simply execute:
```
vagrant up --provider virtualbox
``` 

Viola! A new VM is created with everything installed.
Namely, 
(1) Django and all its python dependencies are installed, 
(2) javascript dependencies are installed and 
(3) Celery addon is configured and running.
Please note that Django web server is still shut down at this point.

### What do I need to configure?
Well, everything regarding Wrapper itself is installed at this point,
but in order to be able to fully utilize application, you'll need
Cloudify Manager running somewhere on your network (setting this up is not a part of this README). 
Then tell the Wrapper about Cloudify Manager endpoint in file
dice_deploy_django/dice_deploy/settings.py by setting variable ```CFY_MANAGER_URL```.

### How to actually run Wrapper?
Navigate to dice_deploy_django folder and run 
```
vagrant ssh
cd dice_deploy_django
python manage.py runserver 0.0.0.0:8000
```
Now the web GUI is available at `localhost:7080` from your host machine.
Direct access to REST API is given at `localhost:7080/docs`.
Visualization of your asynchronous tasks is available at `localhost:8055`.


## Developing with PyCharm
PyCharm supports Vagrant-powered development. You need to set 
project interpreter to point to remote python interpreter at vagrant instance.


## Blueprint-driven Setup
Besides Vagrant it is also possible to use Cloudify Manager to provision Wrapper.

### How do I install/uninstall it?
Basically you need to compress folder `install` into `install.tar.gz` and
upload it to Cloudify Manager, but of course we have a script for this.

There are currently two blueprints available that make deploying this tool
relatively painless. Both blueprints should be uploaded to manager, running on
platform of choice. Due to some loose ends in Flexiant plugin for Cloudify,
credentials need to be specified in blueprint.

After any modifications have been made, execute `./up.sh`, passing
selected platform as an argument. Or simply run the script and follow
instructions.

Removing deploy is as easy as running `./dw.sh`.

### How do I run it?
Move into `dice_deploy_django` folder. There is a `run.sh` script that should
be used to run application.

First, we need to reset application state. Do this by executing:
```
./run.sh reset
```

After reseting is done, execute:
```
./run.sh
```
to spawn one celery worker and then run development server. 
To stop worker and server, press `ctrl + c` to interrupt django 
development server and script
will take care of celery worker.

For more details about operations, consult `run.sh` source code.


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
$ ./dice-deploy-cli use 10.10.20.35:8000
```

The latter option creates a file `.dice-deploy-url` to contain the URL.

Next, we can create a container. This is a virtual designation in the deployment
tool, which can receive up to one blueprint to be deployed. A container can
be created with an optional description and is referenced by its
`container-uuid`:

```bash
$ ./dice-deploy-cli create "Acceptance test environment"
Creating a new container ... DONE.
Container UUID: 02bba363-fb85-4a54-8a2f-f1a11a25ad9d
```

We now have a container known with the UUID `02bba363-fb85-4a54-8a2f-f1a11a25ad9d`.
We can use it to push a blueprint.

```bash
$ ./dice-deploy-cli deploy b0e1b028-8a8c-408c-b619-206257c20481 ../example.tar.gz 
Creating a new deployment ... DONE.
Deployment UUID: b0e1b028-8a8c-408c-b619-206257c20481
```

The command both loads the blueprint in the container and starts the deployment
process. A subsequent call to the same command will have replaced the blueprint,
first uninstalling the existing blueprint and then creating and deploying the
new one.

At any time that we have a valid deployment UUID we can check for the status of
the deployment. 

```bash
$ ./dice-deploy-cli status b0e1b028-8a8c-408c-b619-206257c20481
Obtaining deployment status ...
uploaded
```

Once the blueprint deploys, the returned status will be `deployed`. At this 
point we can obtain the deployment's outputs. The outputs
are the values, which depend on the configuration of the blueprint and the
dynamic values such as dynamically assigned addresses or ports. Please note
that the command expects the container's ID, not the inner deployment's:

```bash
$ ./dice-deploy-cli outputs 02bba363-fb85-4a54-8a2f-f1a11a25ad9d | python -mjson.tool
{
  "outputs": {
    "storm_nimbus_gui": "http://172.16.95.145:8080",
    "zookeeper_endpoint": "172.16.95.148:2181"
  }
}
```

When we want to free the resources created by the deploy, we can call the tear
down action on the blueprint:

```bash
$ ./dice-deploy-cli teardown b0e1b028-8a8c-408c-b619-206257c20481
Deleting deployment ... DONE.
```

Finally, we can also delete the container.

```bash
$ ./dice-deploy-cli delete 02bba363-fb85-4a54-8a2f-f1a11a25ad9d
Deleting container ... DONE.
```


## Managing asynchronous task runner

We use Celery framework for asynchronous command execution. There are upstart 
services used to simplify management of Celery framework. Namely:
 - `sudo service celery-service start|status|stop` - manages worker that consumes messages from main queue
 - `sudo service celery-dashboard start|status|stop` - runs web server on port 5555 where you can see message queue
 - `sudo service celery-test-service start|status|stop` - manages worker that consumes messages from test queue
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


## Web GUI

Dice deployment REST API comes with simple AngularJS web GUI. Source code
resides in `dice_deploy_django/cfy_wrapper_gui/static`. It is a single-page
website with main page served by Django and subpagas managed by AngularJS.
Please use bower to install Javascript libraries. Simply run
`bower install` while being in project directory. Gui can be accessed at
http://localhost:7080 if using Vagrant default setup.