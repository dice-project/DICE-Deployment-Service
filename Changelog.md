# Changelog

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
