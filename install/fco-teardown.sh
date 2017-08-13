#!/bin/bash

set -e

function if_defined()
{
  local arg=$1; shift

  [[ -z ${!arg} ]] && return
  fco "$@" ${!arg}
}

echo "Checking for state ..."
[[ -f .state.inc.sh ]] || exit 1

echo "Loading state file ..."
. .state.inc.sh

echo "Deleting manager instance ..."
if_defined instance_id server delete -cw

echo "Deleting manager firewall template ..."
if_defined firewall_id firewalltemplate delete -w

echo "Deleting SSH key ..."
[[ -n $key_name ]] && rm -f $key_name.pem
if_defined key_id sshkey delete -w

echo "Cleaning up state ..."
rm -f .state.inc.sh inputs.yaml cloudify.inc.sh
