#!/bin/bash

set -e

cd /home/ubuntu
. venv/bin/activate
cd dice_deploy_django

ctx logger info "Stopping celery workers"
celery multi stop 1
#killall -3 celery

ctx logger info "Stopping Server"
kill $(cat gunicorn.pid)
