# DICE deployment tool

Simple wrapper around Cloudify orchestration tool.


*TODO*:
  - finish section about local development environment
  - finish Vagrant file for development deploy
  - add more in-depth information about OpenStack deploy
  - add flexiant blueprint for deploy


## Important general information

When developing the shell scripts, make sure the line endings that end up in
deployed file are "\n". There is a .gitattributes file in place that should
take care of git side of things on checkout. If you add a sensitive file to
repository, please update .gitattributes as well.


## Developer setup

In order to minimize the effort of getting development environment up
and running, vagrant file, along with simple provisioning scripts is
provided. To get started, simply execute `vagrant up --provider
virtualbox`. This will  create new VM and install all required packages.
Just make sure virtual box is installed and you should be good.

In order to be able to fully utilize application, you'll also need
Cloudify manager running. Instructions on how to do this will be
provided soon;)


## Local development workflow

First, we need to ssh to new VM using `vagrant ssh`. This command should
also activate virtual environment for us.

In order to ease the pain of running development instance of this application,
move into `dice_deploy` folder. There is a `run.sh` script that should
be used to run application.

First, we need to reset application state. Do this by executing
`./run.sh reset`.

After this is all done, execute `./run.sh`. This will spawn one celery
worker and then run development server. To stop worker and server,
simply pres `ctrl + c` to interrupt django development server and script
will take care of celery worker.

For more details about operations, consult `run.sh` source code.


## Deploying wrapper

There are currently two blueprints available that make deploying this tool
relatively painless. Both blueprints should be uploaded to manager, running on
platform of choice. Due to some loose ends in Flexiant plugin for Cloudify,
credentials need to be specified in blueprint.

After any modifications have been made, simply execute `./up.sh`, passing
selected platform as an argument. Or simply run the script and follow
instructions.

Removing deploy is as easy as running `./dw.sh`.
