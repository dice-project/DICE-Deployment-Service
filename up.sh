#!/bin/bash

set -e

# Package application
tar -cvzf install/dice_deploy.tar.gz \
    --exclude='*.swp' \
    --exclude='*.pyc' \
    --exclude='*.log' \
    --exclude='*.pid' \
    --exclude='dice_deploy/db.sqlite3' \
    dice_deploy

# Create blueprint archive
tar -cvzf dd.tar.gz --exclude='*.swp' install

# Deploy
cfy blueprints publish-archive -b dice_deploy -l dd.tar.gz
cfy deployments create -d dice_deploy -b dice_deploy
cfy executions start -d dice_deploy -w install -l
cfy deployments outputs -d dice_deploy
