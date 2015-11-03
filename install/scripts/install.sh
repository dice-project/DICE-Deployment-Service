#!/bin/bash

set -e

# Admin part
ctx logger info "Installing system dependencies"

sudo apt-get update
sudo apt-get install -y \
  rabbitmq-server       \
  python-virtualenv     \
  python-dev

# User part
cd /home/ubuntu

ctx logger info "Installing virtualenv"
virtualenv venv
. venv/bin/activate
pip install -U pip
pip install pip-tools

ctx logger info "Copying application sources"
ctx download-resource dice_deploy.tar.gz /home/ubuntu/dice_deploy.tar.gz
tar -xvf dice_deploy.tar.gz

ctx logger info "Installing application dependencies"
cd dice_deploy
pip-sync

ctx logger info "Adjusting settings"
manager=$(ctx node properties manager)
echo "CFY_MANAGER_URL = \"${manager}\"" > dice_deploy/local_settings.py

ctx logger info "Reseting database"
./run.sh reset

ctx logger info "Install gunicorn"
pip install gunicorn

deactivate
