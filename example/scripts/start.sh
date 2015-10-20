#!/bin/bash

set -e

TEMP_DIR="/tmp"
PYTHON_FILE_SERVER_ROOT=${TEMP_DIR}/python-simple-http-webserver
PID_FILE="server.pid"

ctx logger info "Starting HTTP server from ${PYTHON_FILE_SERVER_ROOT}"

port=$(ctx node properties port)

cd ${PYTHON_FILE_SERVER_ROOT}
ctx logger info "Starting SimpleHTTPServer"
nohup python -m SimpleHTTPServer ${port} > /dev/null 2>&1 &
echo $! > ${PID_FILE}
