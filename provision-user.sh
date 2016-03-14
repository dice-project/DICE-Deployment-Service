#!/bin/sh

cd $HOME

virtualenv venv
. venv/bin/activate
pip install -U pip
pip install pip-tools

echo '. venv/bin/activate' >> .profile

cd dice_deploy_django
pip-sync
bower install
python manage.py migrate
