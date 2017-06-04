#!/bin/bash

set -e

function delete()
{
  local cmd=$1
  local flag=${2:-"${1#delete-}-id"}
  local arg=${3:-${flag//-/_}}

  [[ -z $2 ]] && [[ $1 != delete-* ]] && cmd=delete-$1

  [[ -z ${!arg} ]] && return
  aws ec2 $cmd --$flag ${!arg}
}

echo "Checking for state ..."
[[ -f .state.inc.sh ]] || exit 1

echo "Preparing environment ..."
unset AWS_SUBNET_CIDR
unset AWS_KEY_NAME
unset AWS_MANAGER_GROUP_NAME
unset AWS_DEFAULT_GROUP_NAME
unset AWS_AMI_ID

echo "Loading state file ..."
. .state.inc.sh

echo "Terminating instance ..."
[[ -n $instance_id ]] \
  && aws ec2 terminate-instances --instance-ids $instance_id &> /dev/null \
  && aws ec2 wait instance-terminated --instance-ids $instance_id

echo "Releasing elastic IP address ..."
delete release-address allocation-id

echo "Deleting manager security group ..."
delete delete-security-group group-id manager_group_id

echo "Deleting default security group ..."
delete delete-security-group group-id default_group_id

echo "Deleting subnet ..."
delete subnet

echo "Deleting route table ..."
delete route-table

echo "Detaching gateway ..."
[[ $gateway_attached == true ]] &&  aws ec2 detach-internet-gateway \
  --vpc-id $vpc_id --internet-gateway-id $internet_gateway_id

echo "Deleting gateway ..."
delete internet-gateway

echo "Deleting VPC ..."
delete vpc

echo "Deleting SSH key ..."
[[ -n $AWS_KEY_NAME ]] && \
  aws ec2 delete-key-pair --key-name $AWS_KEY_NAME && \
  rm -f ${AWS_KEY_NAME}.pem

echo "Cleaning up state ..."
rm -f .state.inc.sh inputs.yaml cloudify.inc.sh
