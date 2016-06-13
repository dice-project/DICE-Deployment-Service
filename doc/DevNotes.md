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
