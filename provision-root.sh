#!/bin/sh

apt-get update
apt-get install -y rabbitmq-server python-virtualenv python-dev
rabbitmq-plugins enable rabbitmq_management
service rabbitmq-server restart

# install npm and bower
apt-get install -y npm git
npm install -g bower
if [ ! -f /usr/bin/node ]; then
    ln -s /usr/bin/nodejs /usr/bin/node
fi
