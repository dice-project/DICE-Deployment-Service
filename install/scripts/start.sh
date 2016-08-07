#!/bin/bash

set -e

ctx logger info "Starting DICE Deployment service"

sudo service uwsgi start
