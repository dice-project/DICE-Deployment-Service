#!/bin/bash

set -e

cd /home/ubuntu
. venv/bin/activate
cd dice_deploy

ctx logger info "Starting celery worker"
celery multi start 1 -c 1 -A dice_deploy -l INFO

ctx logger info "Starting server"
port=$(ctx node properties port)
gunicorn --bind 0.0.0.0:${port} \
         --pid gunicorn.pid \
         --daemon \
         --log-file gunicorn.log \
         dice_deploy.wsgi:application
