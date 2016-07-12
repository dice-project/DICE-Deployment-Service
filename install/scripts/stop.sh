#!/bin/bash

set -e

# Break free of cloudify agent virtual env cage
ctx logger info "Break from agent virtual env"
unset VIRTUALENV
export PATH=/usr/bin:$PATH

cd /home/ubuntu
. venv/bin/activate
cd dice_deploy_django

ctx logger info "Stopping celery workers"
celery multi stop main-worker@localhost

ctx logger info "Stopping Server"
kill $(cat gunicorn.pid)
