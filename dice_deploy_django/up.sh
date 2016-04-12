#!/bin/bash

port=8000

celery multi start main-worker@localhost \
    --app=dice_deploy \
    --queues=dice_deploy \
    --broker='amqp://guest:guest@localhost:5672//' \
    --without-gossip --without-mingle --events \
    --config=dice_deploy.settings \
    -c 1 \
    -l INFO

gunicorn --bind 0.0.0.0:${port} \
         --pid gunicorn.pid \
         --daemon \
         --log-file gunicorn.log \
         dice_deploy.wsgi:application

