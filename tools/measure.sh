#!/bin/bash

# Default configuration (can be overloaded from settings.inc.sh)
DDS_CLI=./dice-deploy-cli
CFY_CLI=cfy

# Load user configuration
[[ -f settings.inc.sh ]] && . settings.inc.sh

# Non-user configurable stuff
LOG_FILE=
ERR_FILE=
DUR_FILE=


function ddsw ()
{
  $DDS_CLI "$@" 2>> $ERR_FILE | tee -a $LOG_FILE
}

function cfyw ()
{
  $CFY_CLI "$@" 2>> $ERR_FILE | tee -a $LOG_FILE
}

function log ()
{
  echo "$@" | tee -a $LOG_FILE $ERR_FILE
}

function usage ()
{
  cat <<EOF
Deployment time measuring tool

This tools helps us measure time that is needed to execute one full life cycle
of blueprint while also collecting logs that can be used to do any further
analysis.

In order to achieve this, this tool needs fully configured Cloudify Manager
and DICE deployment service, together with their respective command line
tools.

Deployment service tool is used to gather timings that user experiences when
running deploys while Cloudify tools is used to gather execution logs for each
phase of deployment process (deployment environment creation, installation and
uninstallation).

Usage:
  $0 ITERATIONS MEASUREMENT_STORAGE_DIR CONTAINER_UUID BLUEPRINT_FILE

Example
  ./measure.sh 2 /home/tadej/xlab/dice/measurements/wordcount  \\
    10182f0a-f5ce-4f5f-b5d0-8fc876a707b1 \\
    /home/tadej/xlab/dice/DICE-Deployment-Examples/storm/storm-openstack.yaml
EOF

  [[ -n "$1" ]] && echo -e "\nERROR: $1" && exit 1

  exit 0
}

function sanity_check ()
{
  [[ $# -eq 4 ]] || usage "Missing some parameters."

  local iters=$1 && shift
  local destination=$1 && shift
  local container_id=$1 && shift
  local blueprint=$1 && shift

  which $CFY_CLI &> /dev/null \
    || usage "Missing $CFY_CLI command. Do you have cloudify client installed?"
  # We need grep because cloudify's cli is returning 0 on failure.
  $CFY_CLI status | grep -i failed \
    && usage "Misconfigured cloudify. Run '$CFY_CLI status' for more info."

  which $DDS_CLI &> /dev/null \
    || usage "Missing $DDS_CLI command. Do you have DICE client installed?"
  $DDS_CLI list &> /dev/null \
    || usage "Misconfigured DICE client. Run $DDS_CLI for help."

  which jq &> /dev/null \
    || usage "Missing 'jq' command. Please install it from distro repos."

  local status=$($DDS_CLI status $container_id 2> /dev/null)
  [[ $? -eq 0 ]] || usage "Missing container with id '$container_id'."
  [[ "$status" == "empty" ]] || usage "Selected container is not empty."
  [[ -f "$blueprint" ]] || usage "Missing blueprint file ($blueprint)."
}

function execute_deploy ()
{
  local container_id=$1 && shift
  local blueprint=$1 && shift

  ddsw deploy $container_id $blueprint
  ddsw wait-deploy $container_id
}

function obtain_deployment_id ()
{
  local container_id=$1 && shift

  ddsw container-info $container_id | jq -r '.blueprint.id'
}

function execute_teardown ()
{
  local deployment_id=$1 && shift

  cfyw executions start -w uninstall -d $deployment_id &> /dev/null
}

function clean_container ()
{
  local container_id=$1 && shift

  local s=$(ddsw status $container_id)
  if [[ "$s" != "empty" ]]
  then
    ddsw teardown $container_id
    ddsw wait-deploy $container_id
  fi
}

function download_logs ()
{
  local workdir=$1 && shift
  local deployment_id=$1 && shift

  # Ugly line ahead
  local execs=$(cfyw executions list -d $deployment_id | tail -n +7 \
                  | grep "|" | cut -d"|" -f2)
  local e
  for e in $execs
  do
    cfyw events list --json -l -e $e > "$workdir/$e.events"
  done
}

function execute_single_run ()
{
  local workdir=$1 && shift
  local container_id=$1 && shift
  local blueprint=$1 && shift

  log "  deploy"
  SECONDS=0
  execute_deploy $container_id $blueprint
  echo "install: $SECONDS" >> $DUR_FILE

  local deployment_id=$(obtain_deployment_id $container_id)

  log "  teardown"
  SECONDS=0
  execute_teardown $deployment_id
  echo "teardown: $SECONDS" >> $DUR_FILE

  download_logs $workdir $deployment_id

  log "  cleanup"
  SECONDS=0
  clean_container $container_id
  echo "cleanup: $SECONDS" >> $DUR_FILE
}

function find_last_run ()
{
  local basedir=$1 && shift

  local run_folder=$(find $basedir -type d -name 'run-*' | sort -r | head -n1)
  [[ "x$run_folder" == "x" ]] && echo 0 && return 0

  local run_name=${run_folder##*-}
  echo $((10#$run_name))
}

function execute_all_runs ()
{
  local n=$1 && shift
  local basedir=$1 && shift
  local container_id=$1 && shift
  local blueprint=$1 && shift

  mkdir -p $basedir
  local last_run=$(find_last_run $basedir)

  local i workdir
  for i in $( seq -f "%05g" $((last_run + 1)) $((last_run + n)) )
  do
    log "Executing measurement $i:"
    workdir="$basedir/run-$i"
    mkdir $workdir
    LOG_FILE="$workdir/output.out"
    ERR_FILE="$workdir/output.err"
    DUR_FILE="$workdir/durations.txt"

    execute_single_run $workdir $container_id $blueprint
  done
}

function main ()
{
  execute_all_runs "$@"
}


# Parameter checks
sanity_check "$@"
main "$@"
