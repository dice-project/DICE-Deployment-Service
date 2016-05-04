#!/bin/bash

set -e

function get_platforms ()
{
  echo $(find install -iname '*.yaml' -exec basename {} .yaml \;)
}

PLATFORMS="$(get_platforms)"
NAME=$0
TOOLDIR="$(dirname $0)"

function usage ()
{
  cat << EOF

USAGE:

  $NAME PLATFORM

Available platforms: $PLATFORMS

EOF
}

function check_inputs ()
{
  [ -e "$TOOLDIR/inputs-$1.yaml" ] && return
  echo "Please create a valid inputs-$1.yaml file."
  echo ""
  echo "E.g.:"
  echo "cp $TOOLDIR/install/inputs-$1-example.yaml $TOOLDIR/inputs-$1.yaml"
  echo "${EDITOR-nano} $TOOLDIR/inputs-$1.yaml"
  exit 2
}

function check_args ()
{
  for i in $PLATFORMS
  do
    [[ "x$1" == "x$i" ]] && check_inputs $1 && return
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
  DEPLOY_NAME=${2-dice_deploy}

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
  cfy blueprints publish-archive -b $DEPLOY_NAME -l dd.tar.gz -n $blueprint
  echo "Creating deploy"
  cfy deployments create -d $DEPLOY_NAME -b $DEPLOY_NAME -i "$TOOLDIR/inputs-$1.yaml"
  echo "Starting execution"
  cfy executions start -d $DEPLOY_NAME -w install -l
  echo "Outputs:"
  cfy deployments outputs -d $DEPLOY_NAME
}

check_args $1

main $1 $2
