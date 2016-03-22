#!/bin/bash

set -e

ctx logger info "Host name setting, hack key update"
echo "127.0.1.1 $HOSTNAME" | sudo tee -a /etc/hosts
echo "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAsrH2o/WY+DLTJ/gxzIIV4slSkk0b+qQTteIDYidjcSdl0sp5HaE3UVhJ0xRP3LSVK4+SKC6LW/42N6/XzXX1V+O0CmAEVXxfhu97ZMbK1C8+iyo4bNVzabgI5pzUIAsh8c8WWBMgrey5O9MJkzDv8heZaauB+C1uw6G/uF5fFrhvYGVPokb1YaFKsq0cqkPG6usINByxPmgDV2LIHXkPKMktodyGFXmvk+Z9wWqVEzyzaQbnarXXaTd73LupFJAJBQdwm08LCasDs/sunSrr9m4KxDv+sKN0ybxZFjPIOrK2fUzMF1t6u4WTsdZ107G6u/KieEuMlchGVbJ3UDMsnQ== matej@virtubuntutej" >> ~/.ssh/authorized_keys

# Admin part
ctx logger info "Installing system dependencies"

sudo apt-get update
sudo apt-get install -y \
  rabbitmq-server       \
  python-virtualenv     \
  python-dev            \
  npm                   \
  git
sudo npm install -g bower
if [ ! -f /usr/bin/node ]; then
    sudo ln -s /usr/bin/nodejs /usr/bin/node
fi


# User part
cd /home/ubuntu

ctx logger info "Installing virtualenv"
# remove it first to make the operation indempotent
[ -e venv ] && rm -rf venv
virtualenv venv
. venv/bin/activate
pip install -U pip
pip install pip-tools

ctx logger info "Copying application sources"
ctx download-resource dice_deploy.tar.gz /home/ubuntu/dice_deploy.tar.gz
tar -xvf dice_deploy.tar.gz

ctx logger info "Installing application dependencies"
cd dice_deploy_django
pip-sync

ctx logger info "Installing bower"
echo 3 | bower install

ctx logger info "Adjusting settings"
manager=$(ctx node properties manager)
echo "CFY_MANAGER_URL = \"${manager}\"" > dice_deploy/local_settings.py

ctx logger info "Reseting database"
bash run.sh reset

ctx logger info "Install gunicorn"
pip install gunicorn

deactivate
