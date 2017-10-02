#!/bin/bash

set -e

readonly logfile=openstack-teardown-$(date "+%Y-%m-%d-%H-%M-%S").log

function log()
{
  echo "$@" | tee -a $logfile
}

function if_defined()
{
  local arg=$1; shift

  [[ -z ${!arg} ]] && return
  "$@" ${!arg} &>> $logfile
}

function delete_instance()
{
  nova delete $1
  while nova show $1
  do
    sleep 1
  done
}

function delete_key()
{
  nova keypair-delete $1
  rm -f $1.pem
}

log "Checking for state ..."
[[ -f .state.inc.sh ]] || exit 1

log "Loading state file ..."
. .state.inc.sh

log "Terminating instance ..."
if_defined instance_id delete_instance

log "Releasing floating IP address ..."
if_defined public_ip_id neutron floatingip-delete

log "Deleting manager security group ..."
if_defined manager_group_id neutron security-group-delete

log "Deleting default security group ..."
if_defined default_group_id neutron security-group-delete

log "Removing router from subnet"
[[ -n $router_id ]] && [[ -n $subnet_id ]] && \
  neutron router-interface-delete $router_id $subnet_id &> $logfile

log "Deleting router"
if_defined router_id neutron router-delete

log "Deleting subnet ..."
if_defined subnet_id neutron subnet-delete

log "Deleting network ..."
if_defined network_id neutron net-delete

log "Deleting SSH key ..."
if_defined key_name delete_key

log "Cleaning up state ..."
rm -f .state.inc.sh inputs.yaml cloudify.inc.sh
