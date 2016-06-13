# Using DICE deployment service

## Command line tool

The DICE deployment tool comes with a helper utility `dice-deploy-cli` available
in the `tools/` subdirectory. Use it to manually manage the containers and 
deployments. Also use this tool in the automation such as a Continuous
Integration. Please refer to the 
[Getting the DICE deployment service](AdminGuide.md#getting-the-dice-deployment-service)
for instructions on how to obtain the tool

The tool first expects the DICE deployment service URL to be set. This is
possible either through setting the environment variable `DICE_DEPLOY`:

```bash
$ export DICE_DEPLOY=10.10.20.35:8000
```

or by using the action `use`:

```bash
$ dice-deploy-cli use http://10.10.20.35:8000
```

This creates a file `.dice-deploy-url` to contain the URL.

Next, we need to authenticate the client with the service. The user name and
password portions are set by the administrator in the service deployment input
files. Let us assume that the credentials consist of a user name `user` and
password `pwd434`. We supply these credentials to the command line tool:

```bash
$ dice-deploy-cli authenticate user pwd434
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
$ dice-deploy-cli create "Acceptance test environment"
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
$ dice-deploy-cli deploy $CONTAINER_UUID ../example.tar.gz 
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
$ dice-deploy-cli status $DEPLOYMENT_UUID
Obtaining deployment status ...
uploaded
```

In scripts, it is also useful to be able to wait for the deployment process to
finish before being able to proceed with the deployed application. The CLI
tool provides action `wait-deploy`, which blocks the execution of a script,
internally looping until the deployment either succeeds or finishes with an
error:

```bash
$ dice-deploy-cli wait-deploy $CONTAINER_UUID
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
$ dice-deploy-cli outputs $CONTAINER_UUID | python -mjson.tool
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
$ dice-deploy-cli teardown $DEPLOYMENT_UUID
Deleting deployment ... DONE.
```

Finally, we can also delete the container.

```bash
$ dice-deploy-cli delete $CONTAINER_UUID
Deleting container ... DONE.
```

## Command line tool action reference

Complete reference documentation is displayed when the tool is invoked with no
arguments. To get more in-depth documentation with examples for specific
command, use `dice-deploy-cli help COMMAND`.

### General actions

* `help`: display help
  * parameters: [command]
  * example: `dice-deploy-cli help`
  * example: `dice-deploy-cli help deploy`

* `use`: use the URL as the DICE deployment service URL
  * parameters: url
  * example: `dice-deploy-cli use http://109.231.122.46:8000`

* `authenticate`: provide username and password to obtain the authentication token
  * parameters: username password
  * example: `dice-deploy-cli authenticate testuser 123456`

### Container actions

These actions (except for `create`) require the container's UUID as a parameter.

* `create`: creates a new container
  * parameters: description (optional)
  * returns: container-uuid
  * example: `dice-deploy-cli create`
  * example: `dice-deploy-cli create "Smart Energy streaming application"`

* `deploy`: creates a new deployment in the container
  * parameters: container-uuid package-file-name
  * returns: deployment-uuid
  * example: `dice-deploy-cli deploy $CONTAINER_UUID pi-cluster.tar.gz`

* `wait-deploy`: after calling deploy, this will block until deploy finishes
  * parameters: container-uuid
  * example: `dice-deploy-cli wait-deploy $CONTAINER_UUID`

* `container-info`: reports container state
  * parameters: container-uuid
  * returns: container information
  * example:  `dice-deploy-cli container-info $CONTAINER_UUID`

* `delete`: deletes an existing container
  * parameters: container-uuid
  * example: `dice-deploy-cli delete $CONTAINER_UUID`

* `outputs`: get deployment parameters
  * parameters: container-uuid
  * returns: dict of deployment parameters
  * example: `dice-deploy-cli outputs $CONTAINER_UUID`

* `node-ips`: get a list of node IP host addresses in the container
  * parameters: container-uuid
  * returns: list of dictionaries of node properties
  * example: `dice-deploy-cli node-ips $CONTAINER_UUID`

* `nodes`: get a list of nodes and their properties in the container
  * parameters: container-uuid [raw]
  * returns: list of dictionaries of node properties
  * example: `dice-deploy-cli nodes $CONTAINER_UUID`


### Blueprint/deployment actions

These actions require deployment's UUID as a parameter.

* `status`: get deployment status
  * parameters: deployment-uuid
  * returns: the deployment's current status
  * example: `dice-deploy-cli status $DEPLOYMENT_UUID`

* `teardown`: uninstalls and deletes an existing deployment
  * parameters: deployment-uuid
  * example: `dice-deploy-cli teardown $DEPLOYMENT_UUID`


### Input actions

Next two actions make it possible to add and delete inputs on deployment
service.

* `input-add`: add an input that is added to all yamls (not archives!)
  * parameters: key value description
  * returns: dict, representing new input
  * example: `dice-deploy-cli input-add large_flavor_id 654fee342 "flavor"`

* `input-delete`: delete an input
  * parameters: key
  * returns: None
  * example: `dice-deploy-cli input-delete large_flavor_id`
