#!/bin/bash

declare -r -A env_vars=(
  [CFY_ADDRESS]="Address of the VM to contain the Cloudify Manager"
  [CFY_PORT]="Port of the Cloudify Manager's web interface"
  [FCO_CUSTOMER_UUID]="Customer UUID"
  [FCO_USER_UUID]="User account (or API key) UUID for the FCO account"
  [FCO_PASSWORD]="User account password for the FCO account"
  [FCO_VDC_UUID]="UUID of the VDC"
  [FCO_NETWORK_UUID]="UUID of the Network"
  [CFY_AGENT_SSH_KEY_PATH]="Path to the SSH private key to be used by the Cloudify Manager"
  [CFY_AGENT_KEY_UUID]="SSH key ID of the keypair to be used by the Cloudify Manager"
  [CFY_MANAGER_SSH_KEY_PATH]="Path to the SSH private key for connecting to Cloudify Manager"
)

# Helpers
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

  if [ ! -f "$CFY_MANAGER_SSH_KEY_PATH" ]
  then
    echo "Missing the manager ssh key in $CFY_MANAGER_SSH_KEY_PATH"
    success=false
  fi

  $success
}

function sshi()
{
  ssh -i ${CFY_MANAGER_SSH_KEY_PATH} -o IdentitiesOnly=yes "$@"
}

function scpi()
{
  scp -i ${CFY_MANAGER_SSH_KEY_PATH} -o IdentitiesOnly=yes "$@"
}

function cp_key()
{
  local source_path="$1"
  local target_fname=$2

  if [ "$(realpath $source_path)" != "$PWD/$target_fname" ]
  then
    cp "$CFY_MANAGER_SSH_KEY_PATH" $target_fname
  fi

}

# Initial settings and checks
set -e
validate_env

public_ip=$CFY_ADDRESS

echo "Waiting for instance to start accepting ssh connections ..."
i=0
while [[ $i -lt 10 ]]
do
  echo -n "  Attempt $i ... "
  sshi -o ConnectTimeout=1 -o BatchMode=yes -o StrictHostKeyChecking=no \
    centos@$public_ip "echo test" &> /dev/null && break
  echo "failed. Retrying in 10 seconds."
  sleep 10
  i=$(( i + 1 ))
done
echo
[[ $i -eq 10 ]] && "Failed to get instance response in time." && exit 1

# TODO disable "Defaults    requiretty" in /etc/sudoers

if [[ $FCO_ACTIVATE_SWAP == "true" ]]
then
  echo "Activating swap on manager instance ..."
  sshi centos@$public_ip "sudo dd if=/dev/zero of=/swapfile bs=1MB count=6144"
  sshi centos@$public_ip "sudo chmod 0600 /swapfile"
  sshi centos@$public_ip "sudo mkswap /swapfile"
  sshi centos@$public_ip "sudo swapon /swapfile"
  sshi centos@$public_ip \
    "echo /swapfile none swap defaults 0 0 | sudo tee -a /etc/fstab"
fi

echo "Creating DICE plug-in configuration ..."
cat <<EOF > dice-fco.yaml
fco:
  auth:
    url: https://cp.diceproject.flexiant.net
    verify: false
    customer: $FCO_CUSTOMER_UUID
    password: $FCO_PASSWORD
    username: $FCO_USER_UUID
  env:
    vdc_uuid:     $FCO_VDC_UUID
    network_uuid: $FCO_NETWORK_UUID
    agent_key_uuid:    $CFY_AGENT_KEY_UUID
EOF

echo "Preparing the keys"
cp_key "$CFY_MANAGER_SSH_KEY_PATH" cfy-manager.pem
cp_key "$CFY_AGENT_SSH_KEY_PATH" cfy-agent.pem

echo "Uploading DICE configuration to manager VM ..."
sshi centos@$public_ip "sudo mkdir -p /etc/dice"
scpi dice-fco.yaml cfy-agent.pem centos@$public_ip:.
sshi centos@$public_ip "sudo mv dice-fco.yaml /etc/dice/dice.yaml"
sshi centos@$public_ip "sudo chmod 444 /etc/dice/dice.yaml"
sshi centos@$public_ip "sudo mv cfy-agent.pem /root/.ssh/dice.key"
sshi centos@$public_ip "sudo chmod 400 /root/.ssh/dice.key"
rm dice-fco.yaml


echo "Creating bootstrap inputs template ..."
readonly cfy_admin_pass=$(openssl rand -base64 24 | tr "/+=" "_.-")
cat <<EOF > inputs.yaml
public_ip: $CFY_ADDRESS
private_ip: $CFY_ADDRESS
ssh_user: 'centos'
ssh_key_filename: $PWD/cfy-manager.pem

security_enabled: true
ssl_enabled: true
admin_username: admin
admin_password: $cfy_admin_pass
rabbitmq_username: cloudify
rabbitmq_password: $(openssl rand -base64 24 | tr "/+=" "_.-")

ignore_bootstrap_validations: true
EOF

echo "Creating cfy environment file ..."
cat <<EOF > cloudify.inc.sh
export CLOUDIFY_USERNAME=admin
export CLOUDIFY_PASSWORD=$cfy_admin_pass
export CLOUDIFY_SSL_CERT=\
"$PWD/cloudify-manager-blueprints/resources/ssl/server.crt"
EOF
