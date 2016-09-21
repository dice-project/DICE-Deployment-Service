#!/bin/sh

# This file expects that proper environment has been set up before being run.
# Requirements:
#   - cfy command line program
#   - requests python package
#   - cloudify_rest_client python package
#
# This can be achieved by simply running
#
#   virtualenv venv && . venv/bin/activate && pip install cloudify==3.x

SCRIPT_NAME=$0
ROOT="$(dirname $(cd $(dirname $0) && pwd))"

SUPPORTED_PLATFORMS="openstack fco"

declare -A REQUIRED_VARS DUMMY_VARS
REQUIRED_VARS[all]="
  agent_user cfy_manager cfy_manager_username cfy_manager_password
  superuser_username superuser_password superuser_email
"
REQUIRED_VARS[openstack]="medium_image_id medium_flavor_id"
REQUIRED_VARS[fco]="
  service_url username password customer medium_image_id medium_server_type
  medium_disk vdc network agent_key
"
DUMMY_VARS[openstack]="
  small_image_id small_flavor_id
  large_image_id large_flavor_id
"
DUMMY_VARS[fco]="
  small_image_id small_server_type small_disk
  large_image_id large_server_type large_disk
"

function usage ()
{
  cat << EOF
Usage:

  $SCRIPT_NAME platform

Supported platforms: $SUPPORTED_PLATFORMS

Make sure the following environment variables are set:
EOF

  local platform
  local var
  for platform in ${!REQUIRED_VARS[@]}
  do
    echo "  for ${platform}:"
    for var in ${REQUIRED_VARS[$platform]}
    do
      echo "    TEST_${var^^}"
    done
  done

  echo -e "$1" | fold -w 72 -s

  exit 1
}

function check_platform ()
{
  local platform

  for platform in $SUPPORTED_PLATFORMS
  do
    [[ "x$1" == "x$platform" ]] && return 0
  done

  return 1
}

function check_vars ()
{
  local platform_vars="${REQUIRED_VARS[all]} ${REQUIRED_VARS[$1]}"
  local missing=""
  local env_var
  local var

  for var in $platform_vars
  do
    env_var="TEST_${var^^}"
    [[ -z "${!env_var}" ]] && missing="$missing $env_var"
  done

  echo $missing
}

function run_test ()
{
  local tmp_file
  local bootstrap_status
  local test_status
  local teardown_status

  # Create temporary file for communication between processes.
  tmp_file=$(mktemp)

  # Bootstrap dice deployment service
  python bootstrap.py $1 $tmp_file
  bootstrap_status=$?

  if [ "x$bootstrap_status" = "x0" ]
  then
    source $tmp_file
    python -m unittest discover
    test_status=$?
  fi

  if [ "x$bootstrap_status" != "x3" ]
  then
    python teardown.py $tmp_file
    teardown_status=$?
  fi

  # Remove temporary file
  rm -f $tmp_file

  [[ "x$bootstrap_status" = "x0" ]] || return 1
  [[ "x$test_status"      = "x0" ]] || return 1
  [[ "x$teardown_status"  = "x0" ]] || return 1

  return 0
}

function generate_inputs ()
{
  local platform_vars="${REQUIRED_VARS[all]} ${REQUIRED_VARS[$1]}"
  for var in $platform_vars
  do
    env_var="TEST_${var^^}"
    echo "${var}: ${!env_var}"
  done > "$ROOT/inputs-$1.yaml"

  # Add dummy vars to satisfy DICE deployment plugin
  for var in ${DUMMY_VARS[$1]}
  do
    echo "${var}: dummy"
  done >> "$ROOT/inputs-$1.yaml"
}

function main ()
{
  check_platform $1 || usage "ERROR: Invalid/missing platform: '$1'"
  local missing=$(check_vars $1)
  [[ -z "$missing" ]] || usage "ERROR: Missing var(s):\n$missing"

  generate_inputs $1
  run_test $1
}

main "$@"
