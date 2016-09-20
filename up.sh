#!/bin/bash

set -e

function get_platforms ()
{
  echo $(find install -maxdepth 1 -iname '*.yaml' -exec basename {} .yaml \; \
           | grep -v example)
}

PLATFORMS="$(get_platforms)"
NAME=$0
TOOLDIR="$(dirname $0)"

function usage ()
{
  cat << EOF

USAGE:

  $NAME PLATFORM [DEPLOY_NAME]

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
  local name="${1}.yaml"
  local inputs="$TOOLDIR/inputs-${1}.yaml"
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
  cfy blueprints publish-archive -b $deploy_name -l $blueprint -n $name
  echo "Creating deploy"
  cfy deployments create -d $deploy_name -b $deploy_name -i $inputs \
    -i "sources=dds.tar.gz"
  echo "Starting execution"
  cfy executions start -d $deploy_name -w install -l
  echo "Outputs:"
  cfy deployments outputs -d $deploy_name

  rm -f $blueprint
}

check_args $1

main $1 $2
