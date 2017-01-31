DICE Deployment Service tools and utilities
===========================================

This folder contains the utilities and convenience tools for using the DICE
Deployment Service from the command line, prepare and manipulate the blueprints
used in the deployment process. This includes the following tools:

* `dice-deploy-cli`: the bash shell script for invoking the DICE Deployment
  Service's calls. Please refer to the [main documentation](../README.md#command-line-tool)
  for further instructions.
* `update-blueprint-parameters.py`: a Python script for applying configuration
  values to the blueprint. Please refer to
  [this document](./README-update-blueprint-parameters.md)
  for more information.
* `extract-blueprint-parameters.py`: a Python script for extracting parameters
  from a blueprint into a configuration file. Please refer to
  [this document](./README-extract-blueprint-parameters.md) for more information.
* `test-openstack-connection.py`: a Python script for testing if we can connect
  to OpenStack using provided credentials. For usage instructions are
  [here](./README-test-openstack-connection.md).
* `ide_deploy_tosca.sh` packages the blueprint and the resource files, submits
  the blueprint bundle to the deployment service, waits for the deployment to
  finish, and displays the outputs. This script can be used as an IDE build
  target. Further instructions are available [here](./README-ide_deploy_tosca.md)
