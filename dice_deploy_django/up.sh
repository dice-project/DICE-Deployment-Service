#!/bin/bash

echo "I am $(whoami)"

port=${1-8000}
delay=${2-0}

if [ "$delay" != "0" ]
then
    echo "Sleeping for $delay s"
    sleep $delay
fi

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

        # Turn SSL On
#gunicorn --bind 0.0.0.0:${port} \
#         --pid gunicorn.pid \
#         --daemon \
#         --log-file gunicorn.log \
        # --keyfile dice_deploy/certs/gunicorn.key \
        # --certfile dice_deploy/certs/gunicorn.crt \
#         dice_deploy.wsgi:application
