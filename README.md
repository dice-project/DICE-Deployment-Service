# DICE deployment tool

Simple wrapper around Cloudify orchestration tool.


*TODO*:
  - finish section about local development environment
  - finish Vagrant file for development deploy
  - add more in-depth information about OpenStack deploy
  - add flexiant blueprint for deploy
  - update the CLI tool description: polling blueprint status, outputs


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

Basic setting that you need to do is to set cloudify manager url in
dice_deploy_django/dice_deploy/settings.py, variable CFY_MANAGER_URL.


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
$ ./dice-deploy-cli deploy 1b0b97f6-2240-472e-a49d-7362fdc7a638 ../example.tar.gz 
Creating a new deployment ... DONE.
Deployment UUID: b0e1b028-8a8c-408c-b619-206257c20481
```

The command both loads the blueprint in the container and starts the deployment
process. A subsequent call to the same command will have replaced the blueprint,
first uninstalling the existing blueprint and then creating and deploying the
new one.

Once the blueprint deploys, we can obtain the deployment's outputs. The outputs
are the values, which depend on the configuration of the blueprint and the
dynamic values such as dynamically assigned addresses or ports:

```bash
$ ./dice-deploy-cli outputs b0e1b028-8a8c-408c-b619-206257c20481 | python -mjson.tool
{
  "storm_nimbus_gui": {
       "Description": "URL of the Storm nimbus gui",
       "Value": "http://172.16.95.145:8080" }
  "zookeeper_endpoint":{
      "Description": "Debugging endpoint to see if zookeeper lives",
      "Value": "172.16.95.148:2181" }
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
