Blueprint parameter update tool
===============================

Introduction
------------

The aim of this tool is to enable separation of the services'
configuration from the structure of the application. In TOSCA, we express the
individual service's configuration by providing the parameters in the node
template of the node. With this tool it is possible to automate the workflow
of, e.g., the DICE Configuration Optimization, which iteratively produces
new configurations (i.e., new values of the designated parameters under
evaluation) that then need to be fed into the blueprint and deployed for
further evaluation.

Usage example
-------------

To use the tool, we need the following:

* A valid TOSCA blueprint, e.g., `blueprint.yaml`.
* An options file, e.g., `expconfig.yaml`, which declares the variables
  in the configuration file, each associated with a name of a parameter
  and a node name in the blueprint.
* A file containing the configuration values, e.g., `config-matlab.txt`
  if it is a Matlab output, or `config.json` if it is a JSON-formatted
  file.

To update a TOSCA blueprint with new configuration, invoke:

```bash
$ ./update_blueprint_parameters.py \
    --options expconfig.yaml \
    --blueprint blueprint.yaml \
    --configuration config.json \
    --json \
    --output new-blueprint.yaml
```

The result of this call will be the `new-blueprint.yaml` file. Exchange the
configuration with `config-matlab.txt` and use `--matlab` instead of 
`--json` if you use the alternate configuration format.

Input file specification
------------------------

**Blueprint** should be a regular, valid TOSCA blueprint understandable
by the Cloudify orchestrator. Specifically, it should contain a
`node_template` section where the nodes should be named, e.g., `storm`,
`zookeeper` etc.

**Options file** is the same options file used by the Configuration
Optimization. Here is an example of the contents of such a file:

```yaml
# information about the experiment
runexp:
    noise: 1e-5
    numIter: 100
    # ...
# the url of the services confioguration optimization is depend on or use
services:
  deploymentServiceURL: "https://deployment.example.com/"
  monitoringURL: "localhost:4986"
# information about the parameters 
vars:
    - paramname: "component.spout_num"
      node: storm
      options: [1 3]
      lowerbound: 0
      upperbound: 0
      integer: 0
      categorical: 1
    - paramname: "topology.max.spout.pending"
      node: ["storm", "storm_nimbus"]
      options: [1 2 10 100 1000 10000]
      lowerbound: 0
      upperbound: 0
      integer: 0
      categorical: 1
    - paramname: "topology.sleep.spout.wait.strategy.time.ms"
      node: ["storm", "storm_nimbus"]
      # ...
```

Each of the variables definition must include a `paramname` key,
providing the name of the parameter. It also needs to provide a
`node` key, containing one of the following values:

* A string representing the name of the node in the blueprint's node
  templates section. The tool will assign the variable as a parameter
  only to the node template with the provided name.
* An array of strings. Each string in the array has to be the name
  of a node template. In this case, all the node templates that have
  their names listed in the array will get an updated configuration
  with the name defined in `paramname`.

**Configuration file** contains an array of numeric values, where the index 
(i.e., the position in the array) of a value corresponds to the index of the
parameter's declaration in the `vars` array of the options file. Currently
supported formats are JSON and matlab-like. A valid example of a JSON file
is as follows:

```json
{"config": [3, 100, 1, 15.4, 30, 100]}
```

The same configuration file in matlab-like format would appear as follows:

```
    3
    100
    1
    15.4
    30
    100
```

A scientific notation (e.g., `1.554E4`) is also possible.

It is also possible to have configuration files where not all of the parameter
values are present. This can be expressed with a value `null` in the JSON
notation, or as `NaN` in the matlab notation. The tool will treat the missing
values by omitting the corresponding parameters from the node template's
configuration list. More specifically, 

* if a parameter is present in the blueprint, but its corresponding
  configuration value is missing, then the parameter will not appear in
  any of the prescribed node template's configuraton of the updated blueprint
  (removal of the parameter),
* if a paremeter is not present in the blueprint, then it won't appear in the
  updated blueprint either.

The expected effect of the missing parameters on the deployer is then that a
default value will be used if one is present (but this is not expressed in
the blueprint), or it won't be used at all.