# Changelog

## 0.3.4

* Added option for application registration with DMon
* Fixed required blueprint inputs detection
* Migrated task processing to Celery 4 that offers better herror handling
  and reporting capabilities
* Added support for accessing Cloudify Manager over https
* Only allow access to the DICE Deployment service over https
* Migrated installation blueprint to latest DICE TOSCA library


## 0.3.3

* Added better validation of sent files and better errorr messages of
  the validation problems
* Raised the upload file size limit to accommodate for larger blueprint
  bundles
* Fixed a problem where the deployment service returned an error for
  inputs that are not required by the blueprint or when a default was
  available
* Documented bootstrapping a more secure version of Cloudify Manager
* Added documentation for bootstrap services in the FCO
* Added prototype CLI utils for running DICER and for deploying
  from deployment document in xmi via DICER to deployer
* Added a blueprint helper option to dump processed blueprint to a 
  unified json
* Fixed 403 errors when sending bundles of blueprint with a workaround
  to the created folder rights problem in Cloudify Manager


## 0.3.2

* Enabled a smarted blueprint input handling, properly combining any inputs
  supplied with the blueprint with the ones handled by the deployment service
* Updated Chef cookbook and recipe names to conform with standard Chef
  way of naming things
* Added blueprint inspection tool, currently reporting the list of inputs
  expected by the selected blueprint
* Enabled bash completion for CLI tool
* Migrated deployment service bootstrap to Chef

## 0.3.1

* Replaced gunicorn with uWSGI. The default ports for the deployment tools are
  now standard HTTP(S) ports.
* Improved handling of containers, which now behave atomically.
* Improved management of uploaded blueprints. Better validation of blueprints
  discovers early a wider range of blueprint faults.
* Updated API to move most of actions to container resources instead of
  blueprint resources. Some of frequently used blueprint resources are still
  available for backwards compatibility, but internally they are mapped to
  actions on a container.
* Switched to OpenAPI documentation in Swagger.
* Better error reporting in API and on GUI.
* Containers are now able to indicate if they are busy processing a task or
  idle.
* Improved installation procedure for Cloudify 3.4.0
* Unify the naming schemes of the tools: Dashes instead of underscores for
  configuration optimization support.
* Improved unit tests and added deployment tests.
* Used upstart jobs for all services.
* Enabled a debug mode, which opens celery flower on port 5555.

## 0.2.4

* Enabled support and documentation for Cloudify 3.4.0.
* Added an integration test for bootstrapping the DICE deployment service
  wrapper.
* Added an OpenStack tester tool to assess viability of successful bootstrapping
  in the target OpenStack testbed.

## 0.2.3

Add test blueprints and usage documentation
Main purpose of test blueprints is to make sure service is installed properly
and that all of the components are wired together in functional composition.

## 0.2.2

Expand CO use case explanation with REST
* The Configuration Optimization process document now provides
  details about the RESTful calls to be made at various steps
  of the process.

## 0.2.1

Clean up the scripts
* Removes the delayed start attempts.
* Now creates a start script to be called via the SSH.
* Fixes the pip-sync problems to follow Tadej's update
  a few days ago.

## 0.2.0 DICE Y1 review release

This release contains improvements of the DICE deployment service, including:

* Web GUI enables access to most of the DICE deployment service functionality,
  including adding and removing containers, uploading of blueprints, monitoring
  the status of deployment, undeploying, etc.
* Extended functionality available also through the command line interface tool.
* Blueprint related inputs can now be set in the deployment service.
* DICE deployment service bootstrap (deployment) blueprints available for
  OpenStack and FCO.


## 0.1.0 Initial release version

DICE Deployment Service initial version

This version supports the basic functionality of the DICE deployment service.
It provides the RESTful API towards the users, and relies on the Cloudify
Manager 3.2 or 3.3.
