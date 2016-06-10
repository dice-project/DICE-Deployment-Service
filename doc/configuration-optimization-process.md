# Doing configuration optimization using DICE Deployment Service

This document describes general workflow of configuration optimization.  It
uses Apache Storm with simple word count topology as an example and
demonstrates how to execute each step that is required to achieve the final
goal.


## Prerequisites

First thing we need to to is make sure that we have

  * access to DICE Deployment Service (URL and credentials),
  * container available to us on DICE Deployment service (UUID) and
  * a UNIX-y machine available with python version 2 and git installed.

When these requirements are met, we can proceed with installation of tools.


## Getting tools installed

In order to be able to extract information from blueprints and place updated
information back in, there are some handy tools available in deployment
service git repo. So let us checkout this repo and move into `tools` subfolder.

    $ cd ~
    $ git clone https://github.com/dice-project/DICE-Deployment-Service.git
    $ cd DICE-Deployment-Service/tools

Tools require `PyYAML` python package, so make sure that it is installed. In
order to make things a bit more bearable to run, we will also add current
folder to `PATH` and python's module search path:

    $ export PATH="$PATH:$(pwd)"
    $ export PYTHONPATH="$PYTHONPATH:$(pwd)"

This being out of the way, we can continue with doing an initial deploy of
storm cluster.


## Getting sample blueprint and testing initial deploy

Sample blueprint is available at the (DICE Deployment Examples)[1] repository,
so all we need to do is to clone the repo.

    $ cd ~
    $ git clone https://github.com/dice-project/DICE-Deployment-Examples.git
    $ cd storm

In order to make it a bit easier to follow the steps, we will also copy the
blueprint `storm-fco.yaml` to `fco_0.yaml` to separate the source from the
one used in the iterations:

    $ cp storm-fco.yaml fco_0.yaml

[1]: https://github.com/dice-project/DICE-Deployment-Examples

## Getting initial configuration values

In order to extract current configuration parameter values from blueprint, we
first need parameter descriptions. Below is shown excerpt from parameter
description file that is used by extraction tool. There can be additional data
present in this file, but extraction tool will only look at `vars` key that
should contain list of parameter descriptions. As for as extraction tool is
concerned, only required fields in each parameter description are `paramname`
and `node`.

    vars:
      - paramname: "component.spout_num"
        node: storm
        options: [1 3]
        lowerbound: 0
        upperbound: 0
        integer: 0
        categorical: 1
      - paramname: "topology.max.spout.pending"
        node: storm
        options: [1 2 10 100 1000 10000]
        lowerbound: 0
        upperbound: 0
        integer: 0
        categorical: 1

Actual extraction (once we have parameter description stored in `desc.yaml`)
is done by running

    $ extract-blueprint-parameters.py -o desc.yaml -b fco_0.yaml \
        -O values_0.json --json

Extracted values are stored in `values_0.json` file and can be used as an
input to configuration optimization tool.


## Doing iterative improvement to configuration

Getting good combination of configuration parameters needs a few iterations.
We will go manually through steps that compose a single iteration in order to
demonstrate the steps that need to be taken in each iteration. In each
iteration, we use the previously obtaned `values_{i}.json` and `fco_{i}.yaml`.


### Deployment step

Next, we need to set up `dice-deploy-cli` tool by executing:

    $ dice-deploy-cli use <URL of deployment service>
    $ dice-deploy-cli authenticate <username> <password>

Note that these two commands only need to be executed once. Creating initial
deploy is then a matter of executing:

    $ dice-deploy-cli deploy <container id> fco_{i}.yaml

It is then worth waiting until the execution finishes:

    $ dice-deploy-cli wait-deploy <container id>

### Extracting the Strorm topology ID

In case of our sample Apache Storm blueprints, the deployer will have submitted
the Storm topology and provide the unique ID of the job in the deployment's
outputs. To obtain this metadata, run:

    $ dice-deploy-cli outputs <container id>
    DONE.
    {
        "outputs": {
            "storm_nimbus_address": {
                "description": "The address to be used by the storm client",
                "value": "109.231.122.80"
            },
            "storm_nimbus_gui": {
                "description": "URL of the Storm nimbus gui",
                "value": "http://109.231.122.80:8080"
            },
            "wordcount_id": {
                "description": "Unique Storm topology ID",
                "value": "dice-wordcount-1-1465569456"
            }
        }
    }

Please note that we have formatted the example output for legibility. The result
is a JSON file with a single top level key `outputs`. It contains the keys
defined in the `outputs` section of the `fco_{i}.yaml`. For the purposes of the
Configuration Optimization of Storm, we need the `wordcount_id` and the value
of the underlying `value`.

### Extracting performance indicators

Getting performance indicators from existing deploy is out of scope for
deployment tools, so no data acquisition functionality is provided by our
tools. What we do provide is metadata about deployment, such as various
endpoints of deployed services.



### Updating blueprint with new configuration

We will assume here that configuration optimization tool takes
`values_{i}.json` (and any additional data) as input and returns
`values_${i+1}.json` that contains new configuration parameter values.
Incorporating new values into blueprint is done by running

    $ update_blueprint_parameters.py -o desc.yaml -c values_{i+1}.yaml \
        -b fco_{i}.yaml -O fco_{i+1}.yaml --json

This will produce new blueprint `fco_{i}.yaml` that contains new configuration
parameter values.


### Redeploying cluster

Last step is as easy as running

    $ dice-deploy-cli deploy <container id> fco_{i+1}.yaml

This will destroy last deployment and create new one with updated parameters.



