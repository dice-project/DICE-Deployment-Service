#!/bin/bash

declare -r -A env_vars=(
  [OS_EXTERNAL_NETWORK_NAME]="Existing external network"
  [OS_NETWORK_NAME]="Name for newly created network"
  [OS_SUBNET_NAME]="Name for newly created subnet"
  [OS_SUBNET_CIDR]="Subnet CIDR"
  [OS_DNS1]="First DNS server address"
  [OS_DNS2]="Second DNS server address"
  [OS_ROUTER_NAME]="Name for newly created router"
  [OS_KEY_NAME]="SSH key name, used for all spawned VMs"
  [OS_DEFAULT_GROUP_NAME]="Default group name for spawned VMs"
  [OS_MANAGER_GROUP_NAME]="Cloudify Manager group name"
  [OS_SERVER_NAME]="Cloudify Manager server name"
  [OS_IMAGE_ID]="CentOS 7 image id"
  [OS_FLAVOR_ID]="Instance flavor with at least 4 GB of RAM"
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

  if ! openstack network list &> /dev/null
  then
    echo "OpenStack command is not working. Did you source the rc file?"
    success=false
  fi

  if [[ -f .state.inc.sh ]]
  then
    echo "State file exists. Run openstack-teardown.sh first."
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
  ssh -i ${OS_KEY_NAME}.pem -o IdentitiesOnly=yes "$@"
}

function scpi()
{
  scp -i ${OS_KEY_NAME}.pem -o IdentitiesOnly=yes "$@"
}

function os()
{
  openstack "$@" -f value -c id
}

function os_get_id()
{
  # openstack cli malfunctions for some of the calls, hence this ugly hack
  local identifier=$1 ; shift
  openstack "$@" | grep $identifier | awk '{print $2}'
}

function os_get_private_ip()
{
  local inst_id=$1

  openstack server show $inst_id -f value -c addresses \
    | sed 's/=/ /' | awk '{print $2}'
}

function os_get_floating_ip_address()
{
  local floating_ip=$1

  openstack floating ip show $floating_ip -f value -c floating_ip_address
}

# Fix for broken rc files
if [[ -z "$OS_IDENTITY_API_VERSION" ]]
then
  if [[ -n "$OS_PROJECT_ID" ]] # v3
  then
    export OS_INTERFACE=public
    export OS_IDENTITY_API_VERSION=3
  else # v2
    export OS_ENDPOINT_TYPE=publicURL
    export OS_IDENTITY_API_VERSION=2
  fi
fi

# Prepare env
set -e
validate_env
reset_state

readonly external_network_id=$(os network show $OS_EXTERNAL_NETWORK_NAME)

echo "Creating network ..."
readonly network_id=$(os network create $OS_NETWORK_NAME)
state network_id

echo "Creating subnet ..."
set +e # workaround for 'NoneType' object is not iterable error
openstack subnet create \
  --subnet-range $OS_SUBNET_CIDR \
  --network $network_id \
  --dns-nameserver $OS_DNS1 \
  --dns-nameserver $OS_DNS2 \
  $OS_SUBNET_NAME
set -e
readonly subnet_id=$(os_get_id $OS_SUBNET_NAME subnet list)
state subnet_id

echo "Creating router ..."
set +e # workaround for 'NoneType' object is not iterable error
openstack router create $OS_ROUTER_NAME
set -e
readonly router_id=$(os_get_id $OS_ROUTER_NAME router list)
state router_id
set +e # workaround for 'NoneType' object is not iterable error
openstack router set \
  --external-gateway $external_network_id \
  $OS_ROUTER_NAME
set -e

echo "Adding subnet to router ..."
openstack router add subnet $router_id $subnet_id
state router_has_subnet true

echo "Creating SSH key ..."
openstack keypair create $OS_KEY_NAME > $OS_KEY_NAME.pem
state key_name $OS_KEY_NAME
chmod 400 $OS_KEY_NAME.pem

echo "Creating default security group ..."
readonly default_group_id=$(os security group create \
  --description $OS_DEFAULT_GROUP_NAME \
  $OS_DEFAULT_GROUP_NAME
)
state default_group_id
openstack security group rule create \
  --remote-ip "0.0.0.0/0" \
  --dst-port 20 \
  --protocol tcp \
  --ingress \
  $default_group_id

echo "Creating Manager security group ..."
readonly manager_group_id=$(os security group create \
  --description $OS_MANAGER_GROUP_NAME \
  $OS_MANAGER_GROUP_NAME
)
state manager_group_id
for port in 80 443
do
  openstack security group rule create \
    --remote-ip "0.0.0.0/0" \
    --dst-port $port \
    --protocol tcp \
    --ingress \
    $manager_group_id
done
for port in 5672 8101 53229
do
  openstack security group rule create \
    --remote-group $default_group_id \
    --dst-port $port \
    --protocol tcp \
    --ingress \
    $manager_group_id
done

echo "Creating manager instance ..."
readonly instance_id=$(os server create \
  --image $OS_IMAGE_ID \
  --flavor $OS_FLAVOR_ID \
  --security-group $default_group_id \
  --security-group $manager_group_id \
  --key-name $OS_KEY_NAME \
  --nic net-id=$network_id \
  --wait \
  $OS_SERVER_NAME
)
state instance_id
readonly private_ip=$(os_get_private_ip $instance_id)

echo "Adding floating IP to manager ..."
readonly public_ip=$(os floating ip create $external_network_id)
state public_ip
readonly public_ip_address=$(os_get_floating_ip_address $public_ip)
openstack server add floating ip $instance_id $public_ip_address

echo "Waiting for manager to start accepting ssh connections ..."
# TODO the script could get to a screeching halt here if the $public_ip_address
# has previously been added to the known_hosts. Consider adding something like
#ssh-keygen -f "~/.ssh/known_hosts" -R $public_ip_address
# (but by asking the user nicely first) ... except that if I use this I get
# an odd error about mktemp
i=0
while [[ $i -lt 10 ]]
do
  echo -n "  Attempt $i ... "
  sshi -o ConnectTimeout=1 -o BatchMode=yes -o StrictHostKeyChecking=no \
    centos@$public_ip_address "echo test" &> /dev/null && break
  echo "failed. Retrying in 10 seconds."
  sleep 10
  i=$(( i + 1 ))
done
echo
[[ $i -eq 10 ]] && echo "Failed to get instance response in time." && exit 1

# disable "Defaults    requiretty" in /etc/sudoers in CentOS
sshi centos@$public_ip_address -t \
  'sudo sed -i "s/^\(Defaults.\+requiretty\)/#\1/" /etc/sudoers'

if [[ $OS_ACTIVATE_SWAP == "true" ]]
then
  echo "Activating swap on manager instance ..."
  sshi centos@$public_ip_address "sudo dd if=/dev/zero of=/swapfile bs=1MB count=6144"
  sshi centos@$public_ip_address "sudo chmod 0600 /swapfile"
  sshi centos@$public_ip_address "sudo mkswap /swapfile"
  sshi centos@$public_ip_address "sudo swapon /swapfile"
  sshi centos@$public_ip_address \
    "echo /swapfile none swap defaults 0 0 | sudo tee -a /etc/fstab"
fi

echo "Creating DICE-plugin configuration ..."
readonly config_file=dice-openstack.yaml

cat <<EOF > $config_file
openstack:
  env:
    external_network_id: $external_network_id
    internal_network_id: $network_id
    key_name: $OS_KEY_NAME
    default_security_group_name: $OS_DEFAULT_GROUP_NAME
  auth:
    connection:
      auth_url: $OS_AUTH_URL
      username: $OS_USERNAME
      password: $OS_PASSWORD
EOF

if [[ "$OS_IDENTITY_API_VERSION" == 3 ]]
then
  cat <<EOF >> $config_file
      project_id: $OS_PROJECT_ID
      project_name: $OS_PROJECT_NAME
      user_domain_name: $OS_USER_DOMAIN_NAME
EOF
else
  cat <<EOF >> $config_file
      tenant_id: $OS_TENANT_ID
      tenant_name: $OS_TENANT_NAME
EOF
fi

if [[ -n $OS_REGION_NAME ]]
then
  cat <<EOF >> $config_file
    profile:
      region: $OS_REGION_NAME
EOF
fi

echo "Uploading DICE configuration to manager VM ..."
sshi centos@$public_ip_address "sudo mkdir /etc/dice"
scpi $config_file $OS_KEY_NAME.pem centos@$public_ip_address:.
sshi centos@$public_ip_address "sudo mv $config_file /etc/dice/dice.yaml"
sshi centos@$public_ip_address "sudo chmod 444 /etc/dice/dice.yaml"
sshi centos@$public_ip_address "sudo mv $OS_KEY_NAME.pem /root/.ssh/dice.key"
sshi centos@$public_ip_address "sudo chmod 400 /root/.ssh/dice.key"
rm $config_file

echo "Creating bootstrap inputs template ..."
readonly cfy_admin_pass=$(openssl rand -base64 24 | tr "/+=" "_.-")
cat <<EOF > inputs.yaml
public_ip: $public_ip_address
private_ip: $private_ip
ssh_user: 'centos'
ssh_key_filename: $PWD/$OS_KEY_NAME.pem

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
  Manager VM public address: $public_ip_address
  Manager VM private address: $private_ip
  SSH access to VM: ssh -i $OS_KEY_NAME.pem centos@$public_ip_address
-----------------------------------------------------------------------------
EOF
