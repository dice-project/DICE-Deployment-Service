# DICE deployment tool

Simple wrapper around Cloudify orchestration tool.


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

In order to ease the pain of running development instance of this app,
move into `dice_deploy` folder. There is a `run.sh` script that should
be used to run application.

First, we need to reset application state. Do this by executing
`./run.sh reset`.

After this is all done, execute `./run.sh`. This will spawn one celery
worker and then run edvelopment server. To stop worker and server,
simply pres `ctrl + c` to interrupt django development server and script
will take care of celery worker.

For more details about operations, consult `run.sh` souce code.
