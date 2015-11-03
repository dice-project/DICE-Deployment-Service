#!/bin/bash

set -e

cfy executions start -d dice_deploy -w uninstall
cfy deployments delete -d dice_deploy
cfy blueprints delete -b dice_deploy
