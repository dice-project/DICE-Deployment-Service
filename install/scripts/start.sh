#!/bin/bash

set -e

cd /home/ubuntu
. venv/bin/activate
cd dice_deploy_django

ctx logger info "Starting celery worker"
celery multi start 1 -c 1 -A dice_deploy -Q dice_deploy -l INFO
#nohup celery worker -A dice_deploy -Q dice_deploy -n worker-main & 

#ctx logger info "Starting celery dashboard"
##sudo service celery-dashboard start
#nohup celery flower --port=5555 &

sleep 4

ctx logger info "Starting server"
port=$(ctx node properties port)
gunicorn --bind 0.0.0.0:${port} \
         --pid gunicorn.pid \
         --daemon \
         --log-file gunicorn.log \
         dice_deploy.wsgi:application

ctx logger info "Done starting"
