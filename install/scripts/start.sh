#!/bin/bash

set -e

cd /home/ubuntu
. venv/bin/activate
cd dice_deploy_django

ctx logger info "Starting celery worker"
celery multi start main-worker@localhost \
    --app=dice_deploy \
    --queues=dice_deploy \
    --broker='amqp://guest:guest@localhost:5672//' \
    --without-gossip --without-mingle --events \
    --config=dice_deploy.settings \
    -c 1 \
    -l INFO

# make sure that celery has enough time to create queue and everything
sleep 10

ctx logger info "Starting server"
port=$(ctx node properties port)
gunicorn --bind 0.0.0.0:${port} \
         --pid gunicorn.pid \
         --daemon \
         --log-file gunicorn.log \
         dice_deploy.wsgi:application

ctx logger info "Done starting"
