#!/bin/bash

set -e

ctx logger info "Breaking from agent virtual env"
unset VIRTUALENV
export PATH=/usr/bin:$PATH

ctx logger info "Settings hostname"
echo "127.0.1.1 $HOSTNAME" | sudo tee -a /etc/hosts

key=$(ctx node properties ssh_key)
if [[ -n "$key" ]]
then
  ctx logger info "Installing additional ssh key"
  echo "$key" >> /home/ubuntu/.ssh/authorized_keys
fi

ctx logger info "Installing system dependencies"
sudo apt-get update
sudo apt-get install -y \
  rabbitmq-server       \
  nginx                 \
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
rm -rf venv
virtualenv venv
. venv/bin/activate
pip install -U pip

ctx logger info "Copying application sources"
ctx download-resource dice_deploy.tar.gz /home/ubuntu/dice_deploy.tar.gz
tar -xvf dice_deploy.tar.gz

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

ctx logger info "Preparing static files"
python manage.py collectstatic --no-input

ctx logger info "Configuring nginx"
ctx download-resource resources/dice-deployment-service \
  /tmp/dice-deployment-service
sudo cp /tmp/dice-deployment-service /etc/nginx/sites-available
sudo ln -s /etc/nginx/sites-available/dice-deployment-service \
  /etc/nginx/sites-enabled
sudo rm /etc/nginx/sites-enabled/default
rm /tmp/dice-deployment-service
sudo service nginx restart

ctx logger info "Installing uWSGI"
pip install uwsgi
sudo mkdir -p /etc/uwsgi/sites
sudo mkdir -p /var/log/uwsgi
sudo chown ubuntu:ubuntu /var/log/uwsgi
ctx download-resource resources/uwsgi.conf /tmp/uwsgi.conf
sudo cp /tmp/uwsgi.conf /etc/init
rm /tmp/uwsgi.conf
ctx download-resource resources/dice-deployment-service.ini \
  /tmp/dice-deployment-service.ini
sudo cp /tmp/dice-deployment-service.ini /etc/uwsgi/sites
rm /tmp/dice-deployment-service.ini

ctx logger info "Installing Celery service"
sudo mkdir -p /var/log/celery
sudo chown ubuntu:ubuntu /var/log/celery
ctx download-resource resources/celery.conf /tmp/celery.conf
sudo cp /tmp/celery.conf /etc/init
rm /tmp/celery.conf

debug_mode=$(ctx node properties debug_mode)
if [[ "$debug_mode" == "True" ]]
then
  ctx logger info "Installing Flower service"
  ctx download-resource resources/flower.conf /tmp/flower.conf
  sudo cp /tmp/flower.conf /etc/init
  rm /tmp/flower.conf

  ctx logger info "Enabling RabbitMQ web UI"
  sudo rabbitmq-plugins enable rabbitmq_management
  sudo service rabbitmq-server restart
fi

deactivate
