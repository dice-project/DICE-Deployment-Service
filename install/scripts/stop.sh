#!/bin/bash

set -e

cd /home/ubuntu
. venv/bin/activate
cd dice_deploy_django

ctx logger info "Stopping celery worker"
celery multi stop 1

ctx logger info "Stopping Server"
kill $(cat gunicorn.pid)
