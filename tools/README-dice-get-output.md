Utility for getting an output value
===================================

This utility can help with bash scripting steps and actions, which depend on
values assigned by DICE Deployment Service in the TOSCA blueprint outputs.
The script gets outputs from a given virtual deployment container and
extracts a specific output's value.

# Usage

The tool accepts two parameters: the target virtual deployment container ID
`CONTAINER_ID` and the name of the output that we want the value of
`OUTPUT_NAME`. The third parameter is optional, but it provides the tool a
location of the DICE Deployment Service's client configuration (see below).

    $ ./dice-get-output.sh \
        d9d639b0-99dd-405d-8922-920cc55887c5 \
        storm_nimbus_host \
        /etc/dice/my_testbed/.dds.conf

# Jenkins project set up

This script is perfect for scripting Jenkins project build steps. We primarily
created the tool to help us with specific use case, which took two phases.

First, the user deploys a Storm cluster based on a blueprint, which has no
Storm application defined. The blueprint has to define and output for _internal_
IP of the Storm Nimbus host:

```yaml
outputs:
  storm_nimbus_host:
    description: Address of the Storm nimbus to be used in storm client
    value:
      get_attribute: [nimbus_vm, ip]
```

The second Jenkins project is set to submit the Storm application onto this
cluster.

Before creating this project, we need to set up the Jenkins host with the DICE
Deployment Service's tools and utilities. The best way to do that is to use
the Chef cookbooks. After this step, we assume that `dice-deployment-cli` and
`dice-get-output.sh` are accessible to the `jenkins` user from any file system
location.

Next, install the `jq` tool, e.g., in Ubuntu:

    apt-get install jq

We then designate a folder in the Jenknis' home folder to contain the DICE
Deployment Service's local configuration (i.e., the address and the token).
This could be right in the project's workspace, but that might leak the
credentials outside the authorised users. So as a user `jenkins` we create
a folder, say, `~/dice` and set it up with the Deployment Service client:

    $ mkdir -p ~/dice
    $ cd ~/dice
    $ dice-deployment-cli use $DEPLOYMENT_SERVICE_URL
    $ dice-deployment-cli authenticate $USERNAME $PASSWORD

Now we are ready to create a Jenkins project, which has a build step Execute
Shell such as the following:

	CONTAINER_ID="d9d639b0-99dd-405d-8922-920cc55887c5"

	DDS_CONFIG="$HOME/dice/.dds.conf"
	STORM_NIMBUS_HOST=$(dice-get-output.sh $CONTAINER_ID storm_nimbus_host "$DDS_CONFIG")

	TOPOLOGY_CLASSPATH="org.apache.storm.starter.WordCountTopology"
	TOPOLOGY_NAME="wordcount"
	TOPOLOGY_JAR="storm-starter-topologies-1.0.1.jar"

	bash submit-topology.sh \
	    "$TOPOLOGY_JAR" \
	    "$TOPOLOGY_NAME" \
	    "$TOPOLOGY_CLASSPATH" \
	    "$STORM_NIMBUS_HOST"
