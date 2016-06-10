# Blueprint generation templates

This document contains the templates for generating TOSCA documents, which work
with DICE Deployment Service. In this context, the word "template" means a
string of text with interchangeable variables.

The TOSCA blueprint is composed of several parts (`tosca_definitions_version`,
`imports`, `node_templates`, `outputs`), the contents of which depend on the
platform used and the technologies appearing in the blueprint. Conversely, this
document presents relevant parts of the templates.

In each section, there are the mandatory contents, which all have to be in place
for the blueprint to work. Optional parts depend on the users' preferences.

## Common parts

### Language definition version and imports

Variables:

* `PLATFORM`: specifies the platform to deploy the application to. Currently
  supported platforms: `fco`, `openstack`
* `FCO_PLUGIN_VERSION`: specifies the version of the plugin containing the DICE
  technology library definitions, which apply to the FCO platform. (default:
  `master`)
* `FCO_CLIENT_PLUGIN_VERSION`: specifies the version of the plugin, which
  provides support for the FCO platform to Cloudify. (default: `develop`)

*Note*: the `imports` part is still subject to change. How do we specify
OpenStack for the platform?

```yaml
tosca_definitions_version: cloudify_dsl_1_2
 
imports:
  - http://www.getcloudify.org/spec/cloudify/3.3.1/types.yaml
  - https://raw.githubusercontent.com/dice-project/DICE-FCO-Plugin-Cloudify/${FCO_CLIENT_PLUGIN_VERSION}/plugin.yaml
  - http://www.getcloudify.org/spec/chef-plugin/1.3.1/plugin.yaml
  - http://dice-project.github.io/DICE-Deployment-Cloudify/spec/${PLATFORM}/${FCO_CLIENT_VERSION}/plugin.yaml
```

## Zookeeper <a name="zookeeper"></a>

Variables:

* `ZOOKEEPER`: the name of the Zookeeper instance (default: `zookeeper`)
* `ZOOKEEPER_INSTANCE_COUNT`: number of Zookeeper instances, specific to the
  `${ZOOKEEPER}` instance (default: 1)
* `ZOOKEEPER_CONFIGURATION`: a dictionary containing the configuration of the
  `${ZOOKEEPER}` instance. Example: 
  `{"tickTime":1500,"initLimit":10,"syncLimit":5}`

### Node templates

```yaml
  ${ZOOKEEPER}_vm:
    type: dice.hosts.Medium
    instances:
      deploy: ${ZOOKEEPER_INSTANCE_COUNT}

  ${ZOOKEEPER}_quorum:
    type: dice.components.zookeeper.Quorum
    relationships:
      - type: dice.relationships.zookeeper.QuorumContains
        target: ${ZOOKEEPER}_vm

  ${ZOOKEEPER}:
    type: dice.components.zookeeper.Server
    properties:
      configuration: ${ZOOKEEPER_CONFIGURATION}
    relationships:
      - type: dice.relationships.ContainedIn
        target: ${ZOOKEEPER}_vm
      - type: dice.relationships.zookeeper.MemberOfQuorum
        target: ${ZOOKEEPER}_quorum
```

Optional part (tentative version) if the user wants to expose Zookeeper to the
public internet (not a likely scenario):

```yaml
  ${ZOOKEEPER}_firewall:
    type: dice.firewall_rules.Zookeeper

  ${ZOOKEEPER}_virtual_ip:
    type: dice.virtual_ip
```

### Outputs

Optional part (tentative version) if the user wants to expose Zookeeper to the
public internet (not a likely scenario):

*Note*: how will we abstract the `vritual_ip` runtime attribute?

```yaml
  ${ZOOKEEPER}_endpoint:
    description: Public address of the Zookeeper service "${ZOOKEEPER}"
    value: { concat: [ { get_attribute: [${ZOOKEEPER}_virtual_ip, virtual_ip] }, ':2181' ] }
```

## Storm <a name="storm"></a>

Depends on:

* a [Zookeeper](#zookeeper) instance

Variables:

* `ZOOKEEPER`: the name of the Zookeeper instance that this instance of Storm
  will depend on.
* `STORM`: the name of the Storm instance (default: `storm`)
* `STORM_CONFIGURATION`: a dictionary containing the configuration of the
  `${STORM}` instance.
* `STORM_INSTANCE_COUNT`: number of Storm worker instances, specific to the
  `${STORM}` instance (default: 1)
* `STORM_TOPOLOGY_JAR_URL`: the URL or the filename where the user's Storm
   topology can be obtained. If the URL starts with a protocol designation such
   as 'https', then the jar needs to be available for download from the provided
   URL. If no protocol designation is provided, the deployer assumes a file
   packaged with the blueprint (*Note*: we have not implemented this scenario
   yet).
* `STORM_TOPOLOGY_JAR_FILENAME`: the filename of the jar containuing the user's
  Storm topology.
* `STORM_TOPOLOGY_NAME`: the name of the user's Storm topology as it will be
  used in the Storm.
* `STORM_TOPOLOGY_CLASS`: the class name with the main function, which
  implements the Storm topology.

### Node templates

```yaml
  ${STORM}_firewall:
    type: dice.firewall_rules.StormNimbus

  ${STORM}_virtual_ip:
    type: dice.virtual_ip

  ${STORM}_nimbus_vm:
    type: dice.hosts.Medium

  ${STORM}_nimbus:
    type: dice.components.storm.Nimbus
    properties:
      configuration: ${STORM_CONFIGURATION}
    relationships:
      - type: dice.relationships.ContainedIn
        target: ${STORM}_nimbus_vm
      - type: dice.relationships.storm.ConnectedToZookeeperQuorum
        target: zookeeper_quorum

  ${STORM}_vm:
    type: dice.hosts.Medium
    instances:
      deploy: ${STORM_INSTANCE_COUNT}

  ${STORM}:
    type: dice.components.storm.Worker
    properties:
      configuration: ${STORM_CONFIGURATION}
    relationships:
      - type: dice.relationships.ContainedIn
        target: ${STORM}_vm
      - type: dice.relationships.storm.ConnectedToZookeeperQuorum
        target: ${ZOOKEEPER}_quorum
      - type: dice.relationships.storm.ConnectedToNimbus
        target: ${STORM}_nimbus
```

Optional part if the user specifies one or more Storm topologies (jobs) to
submit with the blueprint:

```yaml
  ${STORM_TOPOLOGY}:
    type: dice.components.storm.Topology
    properties:
      application: ${STORM_TOPOLOGY_JAR_URL}
      topology_name: ${STORM_TOPOLOGY_NAME}
      topology_class: ${STORM_TOPOLOGY_CLASS}
   relationships:
     - type: dice.relationships.storm.SubmitTopologyFromVM
       target: ${STORM}_nimbus_vm
     - type: cloudify.relationships.depends_on
       target: ${STORM}
```

### Outputs

```yaml
  ${STORM}_nimbus_address:
    description: The address to be used by the storm client of "${STORM}"
    value: { get_attribute: [${STORM}_nimbus_virtual_ip, ip] }
  ${STORM}_nimbus_gui:
    description: URL of the Storm nimbus gui of "${STORM}"
    value: { concat: [ 'http://', { get_attribute: [${STORM}_virtual_ip, virtual_ip] }, ':8080' ] }
```

Optional:

```yaml
  ${STORM_TOPOLOGY}_id:
    description: Unique Storm topology ID for "${STORM_TOPOLOGY}"
    value: { get_attribute: [ ${STORM_TOPOLOGY}, topology_id ] }
```