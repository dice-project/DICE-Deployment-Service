#!/bin/bash

set -e

ctx logger info "Host name setting, hack key update"
echo "127.0.1.1 $HOSTNAME" | sudo tee -a /etc/hosts
# Matej
echo "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAsrH2o/WY+DLTJ/gxzIIV4slSkk0b+qQTteIDYidjcSdl0sp5HaE3UVhJ0xRP3LSVK4+SKC6LW/42N6/XzXX1V+O0CmAEVXxfhu97ZMbK1C8+iyo4bNVzabgI5pzUIAsh8c8WWBMgrey5O9MJkzDv8heZaauB+C1uw6G/uF5fFrhvYGVPokb1YaFKsq0cqkPG6usINByxPmgDV2LIHXkPKMktodyGFXmvk+Z9wWqVEzyzaQbnarXXaTd73LupFJAJBQdwm08LCasDs/sunSrr9m4KxDv+sKN0ybxZFjPIOrK2fUzMF1t6u4WTsdZ107G6u/KieEuMlchGVbJ3UDMsnQ== matej@virtubuntutej" >> ~/.ssh/authorized_keys
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+DWIPXKhHM+DUdxvglfDMDW3ZOAR56h1CBOYdAod+i563lTwpUirsitmO/JtnIRYGpKfwp6TIVtryAu9hY8kdtE6gr+iq+vFzbPyCsOtZSjx3mk1ySdLy6hV3yFW0Z4o2i4O7/cvkoUZ14lJSwNJhSnQt4jbXmBhy3Wm681UvgszWNMzDL3MreW6zIlJy9MDyuDlyD0kRpAUhyY0uapt9zgbDfKxctHAFyLNV3Gk7f20p3J/Vo/+K3ukkQKy9mh4Upv/aR+muqxaGlWL2kf912QpmoZl8onaXOhb1DnOI8/LWRcwHQ9qcf3Z9/wAFh2I6QfkCMv5byZHs6VeFDWev matej@UbuntuVB" >> ~/.ssh/authorized_keys

# Miha
echo "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEA3Yd5NraU2eXCK+yQdaUIjh6nvVxEZNIuhUfIDxG6mfIanz/8BmJKFv0CtCxLypKKA757HK8A4VMT22OvI016D5v+OfWRg4VfE2mxDXBLVZ5zQyzrVtI3oMYZdg+sgtvY5AeUfqSE5lZhgwb8eIgeQyOdYIfvMSuKLvBEnq6rNDE= miha-WINDOWS" >> ~/.ssh/authorized_keys

# Break free of cloudify agent virtual env cage
ctx logger info "Break from agent virtual env"
unset VIRTUALENV
export PATH=/usr/bin:$PATH

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

ctx logger info "Copying application sources"
ctx download-resource dice_deploy.tar.gz /home/ubuntu/dice_deploy.tar.gz
tar -xvf dice_deploy.tar.gz

#ctx download-resource upstart-services.tar.gz /home/ubuntu/upstart-services.tar.gz
#tar -xvf upstart-services.tar.gz
#sudo cp /home/ubuntu/install/upstart-services/* /etc/init/

ctx logger info "Installing application dependencies"
cd dice_deploy_django
pip install -r requirements.txt

ctx logger info "Installing bower"
bower install

ctx logger info "Adjusting settings"
manager=$(ctx node properties manager)
username=$(ctx node properties manager_user)
password=$(ctx node properties manager_pass)
echo "CFY_MANAGER_URL = \"${manager}\""       >  dice_deploy/local_settings.py
echo "CFY_MANAGER_USERNAME = \"${username}\"" >> dice_deploy/local_settings.py
echo "CFY_MANAGER_PASSWORD = \"${password}\"" >> dice_deploy/local_settings.py

ctx logger info "Resetting database"
superuser_username="$(ctx node properties superuser_username)"
superuser_password="$(ctx node properties superuser_password)"
superuser_email="$(ctx node properties superuser_email)"
bash run.sh reset "$superuser_username" "$superuser_password" \
	"$superuser_email"

ctx logger info "Install gunicorn"
pip install gunicorn

deactivate
