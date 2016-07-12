#!/bin/bash

#remote_ip=$(ctx target instance host_ip)
#
#ssh ubuntu@${remote_ip} ./start.sh

# Break free of cloudify agent virtual env cage
ctx logger info "Break from agent virtual env"
unset VIRTUALENV
export PATH=/usr/bin:$PATH

cd ~ubuntu
./start.sh
