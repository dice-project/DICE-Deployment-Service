#!/bin/bash

set -e

cd /home/ubuntu
. venv/bin/activate
cd dice_deploy_django

ctx logger info "Stopping celery workers"
celery multi stop main-worker@localhost

ctx logger info "Stopping Server"
kill $(cat gunicorn.pid)
