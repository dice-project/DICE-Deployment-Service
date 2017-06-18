# Using DICE deployment service

## Command line tool tutorial

The DICE deployment tool comes with a helper utility `dice-deploy-cli` available
in the `tools/` subdirectory. Use it to manually manage the containers and 
deployments. Also use this tool in the automation such as a Continuous
Integration. Please refer to the 
[Getting the DICE deployment service](AdminGuide.md#getting-the-dice-deployment-service)
for instructions on how to obtain the tool

> **Tip:** `dice-deploy-cli` comes with its own bash completion script.
> Simply source it into your current shell and by executing `. bashcomp` and
> enjoy context aware completions.

The tool first expects the DICE deployment service URL to be set. This is
possible by using the action `use`:

```bash
$ dice-deploy-cli use http://10.10.20.35:8000
[INFO] - Trying to set DICE Deployment Service URL
[INFO] - Checking DICE Deployment Service URL
[INFO] - URL set successfully
```

This creates a file `.dds.conf` to contain the URL.

Next, we need to authenticate the client with the service. The user name and
password portions are set by the administrator in the service deployment input
files. Let us assume that the credentials consist of a user name `user` and
password `pwd434`. We supply these credentials to the command line tool:

```bash
$ dice-deploy-cli authenticate user pwd434
[INFO] - Checking DICE Deployment Service URL
[INFO] - Authenticating
[INFO] - Authorization succeeded
```

This call will obtain and update the `.dds.conf` file with the authentication
token received as a response.
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
[INFO] - Checking DICE Deployment Service URL
[INFO] - Checking DICE Deployment Service authentication data
[INFO] - Creating new container
02bba363-fb85-4a54-8a2f-f1a11a25ad9d
[INFO] - Successfully created new container
```

We now have a container known with the UUID `02bba363-fb85-4a54-8a2f-f1a11a25ad9d`.
Let's save it in an environment variable for convenience:

```bash
$ export CONTAINER_UUID="02bba363-fb85-4a54-8a2f-f1a11a25ad9d"
```

We can use it to push a blueprint.

```bash
$ dice-deploy-cli deploy $CONTAINER_UUID ../examples/test-setup.yaml 
[INFO] - Checking DICE Deployment Service URL
[INFO] - Checking DICE Deployment Service authentication data
[INFO] - Starting blueprint deployment
[INFO] - Successfully started new deploy
```

The command both loads the blueprint in the container and starts the
deployment process. If we would like to register deployed application with
DMon, we must pass `--register-app` flag to the deploy command. We can also
submit some metadata alongside the blueprint by specifying `--metadata` or
`-m` flag (it is possible to specify this flag multiple times to pass more
than one piece of metadata). The command that registers application with DMon
would look something like this:

```bash
$ dice-deploy-cli \
    --register-app \
    -m "meta_key=Meta value" \
    -m "More=meta data" \
    deploy $CONTAINER_UUID ../examples/test-setup.yaml
```

After submitting deployment request, tool does not wait for the deployment to
finish. To track the progress of the request, use the `wait-deploy` action,
which blocks the execution of a script, internally looping until the
deployment either succeeds or finishes with an error:

```bash
$ dice-deploy-cli wait-deploy $CONTAINER_UUID
[INFO] - Checking DICE Deployment Service URL
[INFO] - Checking DICE Deployment Service authentication data
[INFO] - Waiting for deployment to terminate
[INFO] - Container busy, blueprint is uploading_to_cloudify
[INFO] - Container busy, blueprint is uploading_to_cloudify
[INFO] - Container busy, blueprint is preparing_deployment
[INFO] - Container busy, blueprint is preparing_deployment
[INFO] - Container busy, blueprint is installing
[INFO] - Container busy, blueprint is installing
[INFO] - Container busy, blueprint is installing
[INFO] - Container busy, blueprint is installing
# ...
[INFO] - Container busy, blueprint is installing
[INFO] - Container busy, blueprint is installing
[INFO] - Container busy, blueprint is installing
[INFO] - Deployment is done
```

The time for the deployment process to finish depends on complexity of the
blueprint and overall speed of the platform, so it could take anything from
a few minutes on an idle platform to more than an hour on a busy one.

Once the blueprint deploys, we can obtain the deployment's outputs. The outputs
are the values, which depend on the configuration of the blueprint and the
dynamic values such as dynamically assigned addresses or ports. Please note
that the command expects the container's ID, not the inner deployment's:

```bash
$ dice-deploy-cli outputs $CONTAINER_UUID | python -mjson.tool
{
  "outputs": {
    "test_node_1_outputs": {
        "description": "Test node 1 properties",
        "value": "test_property_default_value"
    },
    "test_node_2_outputs": {
        "description": "Test node 2 properties",
        "value": "test_property_value"
    }
  }
}
```

At any time during a container's lifetime, we can also obtain a full status
of the container using `container-info`:

```bash
$ dice-deploy-cli container-info $CONTAINER_UUID | python -mjson.tool
[INFO] - Checking DICE Deployment Service URL
[INFO] - Checking DICE Deployment Service authentication data
[INFO] - Getting information about container 02bba363-fb85-4a54-8a2f-f1a11a25ad9d
[INFO] - Information successfully obtained
{
    "blueprint": {
        "errors": [],
        "id": "367eba48-9c84-403d-940b-6da18c6c3db2",
        "in_error": false,
        "modified_date": "2016-08-16T14:11:51",
        "outputs": {
            "test_node_1_outputs": {
                "description": "Test node 1 properties",
                "value": "test_property_default_value"
            },
            "test_node_2_outputs": {
                "description": "Test node 2 properties",
                "value": "test_property_value"
            }
        },
        "state_name": "deployed"
    },
    "busy": false,
    "description": "Acceptance test environment",
    "id": "02bba363-fb85-4a54-8a2f-f1a11a25ad9d",
    "modified_date": "2016-08-16T14:11:52"
}
```

At this point we can re-issue the `deploy` action with the same or a different
blueprint. The deployment service will tear down the previous deployment and
start a new one.

When we want to free the resources created by the deploy, we can call the tear
down action on the blueprint:

```bash
$ dice-deploy-cli teardown $DEPLOYMENT_UUID
[INFO] - Checking DICE Deployment Service URL
[INFO] - Checking DICE Deployment Service authentication data
[INFO] - Removing deployment from container 02bba363-fb85-4a54-8a2f-f1a11a25ad9d
[INFO] - Deployment removal started successfully
```

Finally, we can also delete the container.

```bash
$ dice-deploy-cli delete $CONTAINER_UUID
[INFO] - Checking DICE Deployment Service URL
[INFO] - Checking DICE Deployment Service authentication data
[INFO] - Deleting container 02bba363-fb85-4a54-8a2f-f1a11a25ad9d
[INFO] - Deletion succeeded
```

## Obtaining status of the virtual deployment container

The command line tool provides actions to obtain the status and runtime-specific
information about the application deployed in a virtual deployment container.

### List deployed instances

Most of the useful blueprints consists of one or more node templates for a
virtual machine (e.g., of type `dice.hosts.Medium`). These usually instantiate
into a compute host or a virtual machine with a local network address. Some
clients or use cases require an insight into a full list of these hosts and
their properties. This is partially possible through authoring the blueprint
into providing runtime information in the outputs, but Cloudify has some
constraints in terms of getting runtime attributes of node templates
instantiating into cardinality larger than 1. Additionally, extending blueprints
may not always be practical, and it would also result in non-standardised naming
of the parameters of interest.

Additionally, we might need an information about what services and other
programs run in each of the nodes. This information is available in the
blueprint for the extraction, but for clients it is simpler to be able to obtain
everything in one bundle.

The action `list-instances` provides this information:

```bash
$ dice-deploy-cli list-instances $CONTAINER_UUID
[INFO] - Checking DICE Deployment Service URL
[INFO] - Checking DICE Deployment Service authentication data
[INFO] - Obtaining VM instances for container 02bba363-fb85-4a54-8a2f-f1a11a25ad9d
  {
    "ip": "109.231.122.34",
        "node_id": "cluster3",
        "id": "cluster3_w878qh",
        "components": [
      "dice.components.cassandra.Worker",
            "dice.hosts.Small"
    ]
  },
    {
    "ip": "109.231.122.197",
        "node_id": "cassandra1_seed_vm",
        "id": "cassandra1_seed_vm_zr6lpy",
        "components": [
      "dice.components.cassandra.Seed",
            "dice.hosts.Small"
    ]
  },
    {
    "ip": "109.231.122.173",
        "node_id": "cluster2",
        "id": "cluster2_gj2x98",
        "components": [
      "dice.components.zookeeper.Server",
            "dice.hosts.Small"
    ]
  },
    {
    "ip": "109.231.122.74",
        "node_id": "cluster1",
        "id": "cluster1_7vq10l",
        "components": [
      "dice.components.storm.Worker",
            "dice.hosts.Small"
    ]
  },
    {
    "ip": "109.231.122.136",
        "node_id": "storm1_master_vm",
        "id": "storm1_master_vm_fmyc8k",
        "components": [
      "dice.components.storm.Nimbus",
            "dice.hosts.Small",
            "dice.components.storm.Topology"
    ]
  }
]
[INFO] - Information successfully obtained
```

## Command line tool action reference

Complete reference documentation is displayed when the tool is invoked with no
arguments. To get more in-depth documentation with examples for specific
command, use `dice-deploy-cli COMMAND -h`.

### General actions

* `use`: use the URL as the DICE deployment service URL
  * parameters: url
  * example: `dice-deploy-cli use http://109.231.122.46:8000`

* `authenticate`: provide username and password to obtain the authentication
  token
  * parameters: username password
  * example: `dice-deploy-cli authenticate testuser 123456`

* `cacert`: Set DICE Deployment Service server certificate
  * parameters: cert
  * example: `dice-deploy-cli cacert pki/deployment-service.cer`

* `get-inputs`: Obtain the service inputs that are currently set globally at the
  DICE Deployment Service
  * example: `dice-deploy-cli get-inputs`

* `set-inputs`: Set (update or replace) the collection of service inputs
   set globally at the DICE Deployment Service
   * parameters: inputs-file
   * example: `dice-deploy-cli set-inputs my-inputs.json`

### Container actions

These actions (except for `create`) require the container's UUID as a parameter.

* `create`: creates a new container
  * parameters: description
  * returns: container-uuid
  * example: `dice-deploy-cli create "Smart Energy streaming application"`

* `deploy`: creates a new deployment in the container
  * parameters: container-uuid package-file-name
  * parameters: container-uuid blueprint-file-name
  * returns: deployment-uuid
  * example: `dice-deploy-cli deploy $CONTAINER_UUID pi-cluster.tar.gz`
  * example: `dice-deploy-cli deploy $CONTAINER_UUID storm.yaml`

* `wait-deploy`: after calling deploy, this will block until deploy finishes
  * parameters: [--poll-interval POLL_INTERVAL_SECONDS] container-uuid
  * example: `dice-deploy-cli wait-deploy $CONTAINER_UUID`
  * example: `dice-deploy-cli wait-deploy --poll-interval 15 $CONTAINER_UUID`

* `container-info`: reports container state
  * parameters: container-uuid
  * returns: container information
  * example: `dice-deploy-cli container-info $CONTAINER_UUID`

* `status`: Obtain container status
  * parameters: container-uuid
  * returns: container status
  * example: `dice-deploy-cli status $CONTAINER_UUID`

* `delete`: deletes an existing container
  * parameters: container-uuid
  * example: `dice-deploy-cli delete $CONTAINER_UUID`

* `outputs`: get deployment parameters
  * parameters: container-uuid
  * returns: dict of deployment parameters
  * example: `dice-deploy-cli outputs $CONTAINER_UUID`

* `list-instances`: List VM instances in container
  * parameters: container-uuid
  * returns: dict of the deployed hosts' properties
  * example: `dice-deploy-cli list_instances $CONTAINER_UUID`

* `teardown`: uninstalls and deletes an existing deployment from the container
  * parameters: container-uuid
  * example: `dice-deploy-cli teardown $CONTAINER_UUID`


### Inputs actions

The following action enables managing the input parameters, which will accompany
each blueprint when it is deployed through the DICE deployment service:

* `set-inputs`: load a new set of inputs to be applicable for any subsequent
  deployments, with the old inputs values being replaced or purged
  * parameters: inputs-json-file
  * example: `dice-deploy-cli set-inputs inputs-openstack.json`
