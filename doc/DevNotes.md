# Development notes

This document contains some guides for prospective developers with the main
aim of making initial setup as simple as possible. We assume that Cloudify
is running at a known network location. See
[Cloudify Management installation](AdminGuide.md#cloudify-management-installation)
for further instructons.

## Vagrant installation

The goal of the Vagrant installation is currently to set up a working
development deployment as quickly as possible. It sets up
a Django project with some javascript libraries for web GUI.
The service internally uses  Celery that enables the application to run
time-consuming tasks asynchronously i.e., after it has already responded with
HTTP response.

To get started, first
[obtain the DICE deployment service release](AdminGuide.md#getting-the-dice-deployment-service)
Then make sure VirtualBox is installed and then execute:
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


## Developing with PyCharm

PyCharm supports Vagrant-powered development. You need to set project
interpreter to point to remote python interpreter at vagrant instance.


## For those who develop in Windows

When developing the shell scripts, make sure the line endings that end up in
deployed file are "\n" i.e. LF and not CRLF. There is a .gitattributes file in
place that should take care of git side of things on checkout. If you add a
sensitive file to repository, please update .gitattributes as well.


## Manually resetting and running the services

Move into `dice_deploy_django` folder. There is a `run.sh` script that should
be used to run application.

First, we need to reset application state. Do this by executing:

    $ ./run.sh reset

After reseting is done, execute:

    $ ./run.sh

to spawn one celery worker, flower web console and django development server.
To stop worker and server, press `ctrl + c` to interrupt django development
server and script will take care of celery worker.

For more details about operations, consult `run.sh` source code.


## Web GUI

Dice deployment REST API comes with simple AngularJS web GUI. Source code
resides in `dice_deploy_django/cfy_wrapper_gui/static`. It is a single-page
website with main page served by Django and subpages managed by AngularJS.
Please use bower to install Javascript libraries. Simply run `bower install`
while being in project directory. Gui can be accessed at http://localhost:7080
if using Vagrant default setup.


### Embedding Web GUI

A simplified version of Web GUI is rendered if you pass container id as a
query parameter. This is particularly useful when rendering container from
Eclipse WebKit plugin. Example url:

    http://localhost:7080?container-id=f4266342-b46b-46b2-8467-cf317eab5a7a


### Debugging Celery Tasks

The simplest way of debugging celery tasks is to force them to execute
synchronously by setting `dice_deploy.settings.CELERY_ALWAYS_EAGER` to `True`.
Any errors will now be visible by developer right in console.

For debugging Celery task queue it is best to use celery-dashboard service.
There you can see all task messages and their statuses. Note that
celery-dashboard service stores all Celery messages into internal database and
displays them from there. It keeps them even after they are dismissed from the
Celery queue. To clear all messages simply restart celery-dashboard service.

There is also log file (tasks.log) in dice_deploy_django folder where tasks
write to.


### Running tests

There are two sorts of tests present in deployment service: unit tests and
integration tests.

Unit tests are stored in application folders under `tests` and are hooked up
to Django's management command. To run unit tests, execute

    $ ./run.sh test

Integration tests are stored in top-level `tests` folder. For usage
instructions, consult accompanying [README.md file][integraton-docs].

[integration-docs]: ../tests/README.md
