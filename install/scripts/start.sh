#!/bin/bash

set -e

cd /home/ubuntu
. venv/bin/activate
cd dice_deploy_django

port=$(ctx node properties port)
ctx logger info "Sending application start to a delayed start"

#nohup bash up.sh $port 60 > /home/ubuntu/startup-nohup.out &

ctx logger info "Up with the service"
bash up.sh $port 60
sleep 5
ctx logger info "Down with the service"
bash down.sh
ctx logger info "Up with the service again"
bash up.sh $port 20


ctx logger info "Done starting"
