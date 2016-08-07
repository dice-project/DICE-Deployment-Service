#!/bin/bash

set -e

ctx logger info "Stopping DICE Deployment service"

sudo service uwsgi stop
