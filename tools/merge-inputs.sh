#!/bin/bash

NAME=$0
TOOLPATH=$(dirname $0)

set -e

function usage()
{
  cat <<EOF

USAGE:

  $NAME INPUTS1 [INPUTS2] OUTPUT

  Merges two JSON files containing inputs for the DICE Deployment Service.
  The main purpose is to update or extend the existing set of inputs with
  another (completely new or partially overlapping) set of inputs.

  INPUTS1 - path to the JSON file containing the new inputs.
  INPUTS2 - path to the JSON file containing the existing inputs. If this
            parameter is omitted, the script fetches the current inputs
            from the DICE Deployment Service instance.
  OUTPUT - path to the JSON file that will contain the result of the merge.

EOF
}

function check_inputs ()
{
  if [ "$1" == "-h" ] || [ "$1" == "--help" ]
  then
    usage
    exit 0
  fi

  if [ "$#" == "2" ] || [ "$#" == "3" ]
  then
    return
  fi

  echo "Invalid number of parameters"
  usage
  exit 1
}

function validate_env()
{
  local success=true

  if ! $TOOLPATH/dice-deploy-cli list &> /dev/null
  then
    echo "The dice-deployment-cli is not working. Have you configured it?"
    success=false
  fi

  $success
}

function main()
{
  local input1="$1" ; shift 1

  if [ "$#" == "1" ]
  then
    validate_env
    local input2="$(mktemp)"
    local has_temp=true

    $TOOLPATH/dice-deploy-cli get-inputs > $input2 2> /dev/null
  else
    local input2="$1" ; shift 1
    local has_temp=false
  fi

  local output="$1" ; shift 1

  $TOOLPATH/merge-inputs.py $input1 $input2 $output

  $has_temp && rm "$input2"
}

check_inputs "$@"
main "$@"
