#!/bin/bash

set -e

function if_defined()
{
  local arg=$1; shift

  [[ -z ${!arg} ]] && return
  openstack "$@" ${!arg}
}

echo "Checking for state ..."
[[ -f .state.inc.sh ]] || exit 1

echo "Loading state file ..."
. .state.inc.sh

echo "Terminating instance ..."
if_defined instance_id server delete --wait

echo "Releasing floating IP address ..."
if_defined public_ip floating ip delete

echo "Deleting manager security group ..."
if_defined manager_group_id security group delete

echo "Deleting default security group ..."
if_defined default_group_id security group delete

echo "Removing router from subnet"
[[ -z ${router_id+x} ]] || [[ -z ${subnet_id+x} ]] || \
  openstack router remove subnet $router_id $subnet_id

echo "Deleting router"
if_defined router_id router delete

echo "Deleting subnet ..."
if_defined subnet_id subnet delete

echo "Deleting network ..."
if_defined network_id network delete

echo "Deleting SSH key ..."
[[ -n $key_name ]] && \
  openstack keypair delete $key_name && rm -f $key_name.pem

echo "Cleaning up state ..."
rm -f .state.inc.sh inputs.yaml cloudify.inc.sh
