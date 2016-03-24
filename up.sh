#!/bin/bash

set -e

function get_platforms ()
{
  echo $(find install -iname '*.yaml' -exec basename {} .yaml \;)
}

PLATFORMS="$(get_platforms)"
NAME=$0

function usage ()
{
  cat << EOF

USAGE:

  $NAME PLATFORM

Available platforms: $PLATFORMS

EOF
}

function check_args ()
{
  for i in $PLATFORMS
  do
    [[ "x$1" == "x$i" ]] && return
  done
  usage

  echo -n "ERROR: "
  if [[ "x" == "x$1" ]]
  then
    echo "Missing platform."
  else
    echo "Invalid platform specified: $1."
  fi
  exit 1
}

function main ()
{
  local blueprint="${1}.yaml"

  # Package application
  tar -cvzf install/dice_deploy.tar.gz \
    --exclude='*.swp' \
    --exclude='*.pyc' \
    --exclude='*.log' \
    --exclude='*.pid' \
    --exclude='dice_deploy/db.sqlite3' \
    --exclude='dice_deploy/uploads' \
    dice_deploy_django

  ## Package the upstart configuration
  #tar -cvzf install/upstart-services.tar.gz \
  #  install/upstart-services

  # Create blueprint archive
  tar -cvzf dd.tar.gz --exclude='*.swp' install

  # Deploy
  echo "Publishing blueprint"
  cfy blueprints publish-archive -b dice_deploy -l dd.tar.gz -n $blueprint
  echo "Creating deploy"
  cfy deployments create -d dice_deploy -b dice_deploy
  echo "Starting execution"
  cfy executions start -d dice_deploy -w install -l
  echo "Outputs:"
  cfy deployments outputs -d dice_deploy
}

check_args $1

main $1
