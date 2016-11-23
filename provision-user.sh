#!/bin/sh

cd $HOME

virtualenv venv
. venv/bin/activate
pip install -U pip

echo '. venv/bin/activate' >> .profile

cd dice_deploy_django
pip install -r requirements-dev.txt
bower install

./run.sh reset
