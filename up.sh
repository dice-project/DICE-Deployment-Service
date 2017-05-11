#!/bin/bash

set -e

NAME=$0
TOOLDIR="$(dirname $0)"

function usage ()
{
  cat << EOF

USAGE:

  $NAME INPUTS [DEPLOY_NAME]

EOF
}

function check_inputs ()
{
  [[ -f "$1" ]] && return

  echo "Please create a valid inputs file."
  echo
  echo "E.g.:"
  echo "cp $TOOLDIR/install/inputs-example.yaml $TOOLDIR/inputs.yaml"
  echo "${EDITOR-nano} $TOOLDIR/inputs.yaml"
  exit 2
}

function main ()
{
  local inputs="$1"
  # :- is not optional here, because function parameters are tricky
  local deploy_name=${2:-dice_deploy}

  # Package application
  git archive -o install/dds.tar.gz --prefix dds/ HEAD dice_deploy_django

  # Create blueprint archive
  local blueprint=dds-blueprint.tar.gz
  tar -cvzf $blueprint install
  rm install/dds.tar.gz

  # Deploy
  echo "Publishing blueprint"
  cfy blueprints publish-archive -b $deploy_name -l $blueprint
  echo "Creating deploy"
  cfy deployments create -d $deploy_name -b $deploy_name -i $inputs \
    -i "sources=dds.tar.gz"
  echo "Starting execution"
  cfy executions start -d $deploy_name -w install -l
  echo "Outputs:"
  cfy deployments outputs -d $deploy_name

  rm -f $blueprint
}

check_inputs $1

main $1 $2
