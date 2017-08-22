#!/bin/bash

declare -r -A env_vars=(
  [CFY_ADDRESS]="Address of the VM containing the Cloudify Manager"
  [CLOUDIFY_USERNAME]="Username for accessing Cloudify Manager"
  [CLOUDIFY_PASSWORD]="Password for accessing Cloudify Manager"
  [ADMIN_EMAIL]="E-mail address of the DICE Deployment Service administrator"
  [UBUNTU_USERNAME]="Linux username for the Ubuntu"
  [CENTOS_USERNAME]="Linux username for the CentOS"
  [SMALL_INSTANCE_ID]="Instance type ID for a small server"
  [MEDIUM_INSTANCE_ID]="Instance type ID for a medium server"
  [LARGE_INSTANCE_ID]="Instance type ID for a large server"
  [UBUNTU_IMAGE_UUID]="Image UUID of the Ubuntu 14.04 OS image"
  [CENTOS_IMAGE_UUID]="Image UUID of the CentOS 7 OS image"
  [FCO_SMALL_DISK_UUID]="FCO UUID of the product offer for disk of small size"
  [FCO_MEDIUM_DISK_UUID]="FCO UUID of the product offer for disk of medium size"
  [FCO_LARGE_DISK_UUID]="FCO UUID of the product offer for disk of large size"
  [DEPLOYMENT_PLATFORM]="Target platform for deployment(s)"
)

set -e

NAME=$0
INSTALLDIR="$(dirname $0)"
TOOLDIR="$INSTALLDIR/../tools"
DEPLOYMENT_ID=${1:-dice_deploy}

function usage ()
{
  cat <<EOF

USAGE:

  $NAME [DEPLOY_NAME]

  Prepares the inputs for deployment of the DICE Deployment Service,
  runs the deployment, and sets up the runtime inputs at the new DICE Deployment
  Service instance.

  DEPLOY_NAME - optional deployment name (default: dice_deploy)

EOF
}

function check_inputs ()
{
  if [ "$1" == "-h" ] || [ "$1" == "--help" ]
  then
    usage
    exit 0
  fi
}

function validate_env()
{
  local success=true

  for v in "${!env_vars[@]}"
  do
    if [[ -z "${!v}" ]]
    then
      echo "Missing variable $v: ${env_vars[$v]}."
      success=false
    fi
  done

  $success
}

validate_env

cd $INSTALLDIR/..

echo "Creating deployment inputs for DICE Deployment Service"
readonly dds_admin_user=admin
readonly dds_admin_pass=$(openssl rand -base64 24 | tr "/+=" "_.-")
cat <<EOF > inputs.yaml
platform: $DEPLOYMENT_PLATFORM
medium_disk_type: $FCO_MEDIUM_DISK_UUID
medium_instance_type: $MEDIUM_INSTANCE_ID
ubuntu_image_id: $UBUNTU_IMAGE_UUID

cfy_manager: $CFY_ADDRESS
cfy_manager_username: $CLOUDIFY_USERNAME
cfy_manager_password: $CLOUDIFY_PASSWORD
cfy_manager_protocol: https
cfy_manager_cacert: cfy.crt

superuser_username: $dds_admin_user
superuser_password: $dds_admin_pass
superuser_email: $ADMIN_EMAIL
enable_debug: ${DDS_ENABLE_DEBUG:-false}

centos_image_id: dummy
dns_server: dummy
large_disk_type: dummy
large_instance_type: dummy
small_disk_type: dummy
small_instance_type: dummy
EOF

echo "Running installation"
./up.sh inputs.yaml $DEPLOYMENT_ID

echo "Obtaining outputs"
OUTPUTS_TO_EVAL=$(python "$INSTALLDIR/outputs-to-env.py" $DEPLOYMENT_ID)

if [ "$?" != "0" ]
then
  echo ""
  echo "ERROR obtaining the outputs. Aborting."
  echo ""

  exit $?
fi

# Here we obtain DDS_DNS_SERVER and DDS_HTTP_ENDPOINT
eval $OUTPUTS_TO_EVAL

echo "Creating DICE Deployment Service's runtime inputs"
cat <<EOF > dds_inputs.json
[
  {
    "key": "dns_server",
    "value": "$DDS_DNS_SERVER",
    "description": "This should be populated with DICE deployment service's private IP. Doing this will ensure that services can discover each other by using FQDNs for addressing."
  },
  {
    "key": "ubuntu_agent_user",
    "value": "$UBUNTU_USERNAME",
    "description": "User that can be used to login to cloud image for Ubuntu images."
  },
  {
    "key": "centos_agent_user",
    "value": "$CENTOS_USERNAME",
    "description": "User that can be used to login to cloud image for CentOS images."
  },
  {
    "key": "small_disk_type",
    "value": "$FCO_SMALL_DISK_UUID",
    "description": "FCO: small disk's product offer UUID. Other platforms: provide dummy value."
  },
  {
    "key": "medium_disk_type",
    "value": "$FCO_MEDIUM_DISK_UUID",
    "description": "FCO: medium disk's product offer UUID. Other platforms: provide dummy value."
  },
  {
    "key": "large_disk_type",
    "value": "$FCO_LARGE_DISK_UUID",
    "description": "FCO: large disk's product offer UUID. Other platforms: provide dummy value."
  },
  {
    "key": "platform",
    "value": "$DEPLOYMENT_PLATFORM",
    "description": "Primary platform (openstack, amazon, fco) to be used by the orchestrator."
  },
  {
    "key": "small_instance_type",
    "value": "$SMALL_INSTANCE_ID",
    "description": "ID of the small server instance type, product offer or flavor."
  },
  {
    "key": "medium_instance_type",
    "value": "$MEDIUM_INSTANCE_ID",
    "description": "ID of the medium server instance type, product offer or flavor."
  },
  {
    "key": "large_instance_type",
    "value": "$LARGE_INSTANCE_ID",
    "description": "ID of the large server instance type, product offer or flavor."
  },
  {
    "key": "ubuntu_image_id",
    "value": "$UBUNTU_IMAGE_UUID",
    "description": "Image id for instances that require Ubuntu."
  },
  {
    "key": "centos_image_id",
    "value": "$CENTOS_IMAGE_UUID",
    "description": "Image id for instances that require Ubuntu."
  },
  {
    "key": "java_version",
    "value": "8",
    "description": "Java version"
  },
  {
    "key": "java_flavor",
    "value": "openjdk",
    "description": "Java flavor"
  },
  {
    "key": "dmon_address",
    "value": "TBA",
    "description": "Place dmon address here (eg. 10.50.51.4:5001). This input is required if one wishes to use monitoring components."
  },
  {
    "key": "logstash_graphite_address",
    "value": "TBA",
    "description": "Place logstash graphite address here (eg. 10.50.51.4:5002). This input is required if one wishes to use monitoring components that utilize graphite logstash input."
  },
  {
    "key": "logstash_lumberjack_address",
    "value": "TBA",
    "description": "Place logstash lumberjack address here (eg. 10.50.51.4:5000). This input is required if one wishes to use monitoring components that utilize lumberjack logstash input."
  },
  {
    "key": "logstash_udp_address",
    "value": "TBA",
    "description": "Place logstash udp address here (eg. 10.50.51.4:25826). This input is required if one wishes to use monitoring components that utilize udp logstash input."
  },
  {
    "key": "logstash_lumberjack_crt",
    "value": "TBA",
    "description": "Content of certificate that is offered by logstash lumberjack address."
  }
]
EOF


cat <<EOF

-----------------------------------------------------------------------------
SUMMARY:
  DICE Deployment Service URL: $DDS_HTTP_ENDPOINT
  Private address of the service: $DDS_DNS_SERVER
  Admin username: $dds_admin_user
  Admin password: $dds_admin_pass
-----------------------------------------------------------------------------
EOF