#!/bin/bash

declare -r -A env_vars=(
  [FCO_VDC_UUID]="UUID of the VDC that will host the instance"
  [FCO_NETWORK_UUID]="UUID of the Network that manager instance will connect"
  [FCO_DISK_OFFER_UUID]="UUID of the disk offer, used to create instance"
  [FCO_SERVER_OFFER_UUID]="UUID of the server offer, used to create instance"
  [FCO_IMAGE_UUID]="UUID of the CentOS image"
  [FCO_KEY_NAME]="Name of the SSH key that will be created"
  [FCO_SERVER_NAME]="Name of the instance that will be created"
  [FCO_MANAGER_TEMPLATE_NAME]="Name of the newly created firewall"
)

# Helpers
function reset_state()
{
  echo > .state.inc.sh
}

function state()
{
  local val="${2:-${!1}}"
  echo "readonly $1=\"$val\"" >> .state.inc.sh
}

function validate_env()
{
  local success=true

  if ! fco vdc list &> /dev/null
  then
    echo "fco command is failing. Did you install and configure fco client?"
    success=false
  fi

  if [[ -f .state.inc.sh ]]
  then
    echo "State file exists. Run fco-teardown.sh first."
    success=false
  fi

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

function sshi()
{
  ssh -i $FCO_KEY_NAME.pem \
    -o IdentitiesOnly=yes \
    -o BatchMode=yes \
    -o UserKnownHostsFile=/dev/null \
    -o StrictHostKeyChecking=no \
    "$@"
}

function scpi()
{
  scp -i $FCO_KEY_NAME.pem \
    -o IdentitiesOnly=yes \
    -o BatchMode=yes \
    -o UserKnownHostsFile=/dev/null \
    -o StrictHostKeyChecking=no \
    "$@"
}

function wrap()
{
  fco "$@" 2> /dev/null
}

# Initial settings and checks
set -e
validate_env
reset_state

echo "Creating SSH key ..."
ssh-keygen -f $FCO_KEY_NAME.pem -N "" -t rsa -q
state key_name $FCO_KEY_NAME
chmod 400 $FCO_KEY_NAME.pem
readonly pubkey=$(echo -n $(cat $FCO_KEY_NAME.pem.pub)) # Remove trailing \n
readonly key_id=$(cat <<EOF | wrap sshkey create -w - | jq -r .itemUUID
{
  "globalKey": false,
  "publicKey": "$pubkey",
  "resourceName": "$FCO_KEY_NAME"
}
EOF
)
state key_id
rm $FCO_KEY_NAME.pem.pub

echo "Creating manager firewall template ..."
# Generating json from bash is ... cumbersome (trying to be family friendly;).
rules="{
  \"action\": \"ALLOW\",
  \"connState\": \"EXISTING\",
  \"direction\": \"IN\",
  \"icmpParam\": \"ECHO_REPLY_IPv4\",
  \"ipAddress\": \"\",
  \"ipCIDRMask\": 0,
  \"localPort\": 0,
  \"name\": \"handshake\",
  \"protocol\": \"ANY\",
  \"remotePort\": 0
}"
for port in 22 80 443 5672 8101 53229
do
  rules="$rules, {
  \"action\": \"ALLOW\",
  \"connState\": \"ALL\",
  \"direction\": \"IN\",
  \"icmpParam\": \"ECHO_REPLY_IPv4\",
  \"ipAddress\": \"0.0.0.0\",
  \"ipCIDRMask\": 0,
  \"localPort\": $port,
  \"name\": \"rule-$port\",
  \"protocol\": \"TCP\",
  \"remotePort\": 0
}"
done
readonly firewall_id=$(cat <<EOF | wrap firewalltemplate create -w - \
  | jq -r .itemUUID
{
  "defaultInAction": "REJECT",
  "defaultOutAction": "ALLOW",
  "firewallInRuleList": [
    $rules
  ],
  "resourceName": "$FCO_MANAGER_TEMPLATE_NAME",
  "type": "IPV4"
}
EOF
)
state firewall_id

echo "Creating manager instance ..."
readonly instance_id=$(cat <<EOF | wrap server create -k $key_id -w - \
  | jq -r .itemUUID
{
  "disks": [
    {
      "productOfferUUID": "$FCO_DISK_OFFER_UUID",
      "resourceName": "${FCO_SERVER_NAME}-disk",
      "size": 0,
      "storageCapabilities": [
        "CLONE",
        "CHILDREN_PERSIST_ON_DELETE",
        "CHILDREN_PERSIST_ON_REVERT"
      ],
      "vdcUUID": "$FCO_VDC_UUID"
    }
  ],
  "imageUUID": "$FCO_IMAGE_UUID",
  "nics": [
    {
      "networkUUID": "$FCO_NETWORK_UUID",
      "resourceName": "${FCO_SERVER_NAME}-nic"
    }
  ],
  "productOfferUUID": "$FCO_SERVER_OFFER_UUID",
  "resourceName": "$FCO_SERVER_NAME",
  "vdcUUID": "$FCO_VDC_UUID"
}
EOF
)
state instance_id
readonly public_ip=$(wrap server get $instance_id \
  | jq -r .nics[0].ipAddresses[0].ipAddress)
wrap firewalltemplate apply -w $firewall_id $public_ip &> /dev/null
wrap server start -w $instance_id &> /dev/null

echo "Waiting for instance at $public_ip to start accepting ssh connections ..."
i=0
while [[ $i -lt 20 ]]
do
  echo -n "  Attempt $i ... "
  sshi -o ConnectTimeout=1 -o BatchMode=yes -o StrictHostKeyChecking=no \
    centos@$public_ip "echo test" &> /dev/null && break
  echo "failed. Retrying in 20 seconds."
  sleep 20
  i=$(( i + 1 ))
done
echo
[[ $i -eq 10 ]] && echo "Failed to get instance response in time." && exit 1

# disable "Defaults    requiretty" in /etc/sudoers in CentOS
sshi centos@$public_ip -t \
  'sudo sed -i "s/^\(Defaults.\+requiretty\)/#\1/" /etc/sudoers'

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
readonly config_file=dice-fco.yaml

cat <<EOF > $config_file
fco:
  auth:
    url: $(jq .url .fco.conf)
    verify: false
    customer: $(jq .customer .fco.conf)
    password: $(jq .password .fco.conf)
    username: $(jq .username .fco.conf)
  env:
    vdc_uuid: $FCO_VDC_UUID
    network_uuid: $FCO_NETWORK_UUID
    agent_key_uuid: $key_id
EOF

echo "Uploading DICE configuration to manager VM ..."
sshi centos@$public_ip "sudo mkdir -p /etc/dice"
scpi $config_file ${FCO_KEY_NAME}.pem centos@$public_ip:.
sshi centos@$public_ip "sudo mv $config_file /etc/dice/dice.yaml"
sshi centos@$public_ip "sudo chmod 444 /etc/dice/dice.yaml"
sshi centos@$public_ip "sudo mv ${FCO_KEY_NAME}.pem /root/.ssh/dice.key"
sshi centos@$public_ip "sudo chmod 400 /root/.ssh/dice.key"
rm dice-fco.yaml

echo "Creating bootstrap inputs template ..."
readonly cfy_admin_pass=$(openssl rand -base64 24 | tr "/+=" "_.-")
cat <<EOF > inputs.yaml
public_ip: $public_ip
private_ip: $public_ip
ssh_user: 'centos'
ssh_key_filename: $PWD/${FCO_KEY_NAME}.pem

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

cat <<EOF

-----------------------------------------------------------------------------
SUMMARY:
  Manager VM public address: $public_ip
  SSH access to VM: ssh -i ${FCO_KEY_NAME}.pem centos@$public_ip
-----------------------------------------------------------------------------
EOF
