#!/bin/bash

declare -r -A env_vars=(
  [AWS_SUBNET_CIDR]="Subnet CIDR"
  [AWS_KEY_NAME]="SSH key name, used for all spawned VMs"
  [AWS_MANAGER_GROUP_NAME]="Cloudify Manager group name"
  [AWS_DEFAULT_GROUP_NAME]="Default group name for spawned VMs"
  [AWS_AMI_ID]="CentOS 7 AMI id"
  [AWS_INSTANCE_TYPE]="Instance type with at least 4 GB of RAM"

  [AWS_DEFAULT_REGION]="AWS region that should be used by manager"
  [AWS_ACCESS_KEY_ID]="AWS access key"
  [AWS_SECRET_ACCESS_KEY]="AWS secret access key"
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

  if [[ -f .state.inc.sh ]]
  then
    echo "State file exists. Run aws-teardown.sh first."
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
  ssh -i ${AWS_KEY_NAME}.pem \
    -o IdentitiesOnly=yes \
    -o BatchMode=yes \
    -o UserKnownHostsFile=/dev/null \
    -o StrictHostKeyChecking=no \
    "$@"
}

function scpi()
{
  scp -i ${AWS_KEY_NAME}.pem \
    -o IdentitiesOnly=yes \
    -o BatchMode=yes \
    -o UserKnownHostsFile=/dev/null \
    -o StrictHostKeyChecking=no \
    "$@"
}

# Prepare env
set -e
validate_env
reset_state

export AWS_DEFAULT_OUTPUT="text"

echo "Creating VPC ..."
readonly vpc_id=$(aws ec2 create-vpc \
  --cidr-block $AWS_SUBNET_CIDR \
  --query 'Vpc.VpcId'
)
state vpc_id

echo "Creating subnet ..."
readonly subnet_id=$(aws ec2 create-subnet \
  --vpc-id $vpc_id \
  --cidr-block $AWS_SUBNET_CIDR \
  --query 'Subnet.SubnetId'
)
state subnet_id
aws ec2 modify-subnet-attribute \
  --subnet $subnet_id \
  --map-public-ip-on-launch

echo "Creating gateway ..."
readonly internet_gateway_id=$(aws ec2 create-internet-gateway \
  --query 'InternetGateway.InternetGatewayId'
)
state internet_gateway_id

echo "Attaching gateway ..."
aws ec2 attach-internet-gateway --vpc-id $vpc_id \
  --internet-gateway-id $internet_gateway_id
state gateway_attached true

echo "Setting up route table ..."
readonly route_table_id=$(aws ec2 create-route-table \
  --vpc-id $vpc_id \
  --query 'RouteTable.RouteTableId'
)
state route_table_id

aws ec2 create-route \
  --route-table-id $route_table_id \
  --destination-cidr 0.0.0.0/0 \
  --gateway-id $internet_gateway_id &> /dev/null

aws ec2 associate-route-table \
  --subnet-id $subnet_id \
  --route-table-id $route_table_id &> /dev/null

echo "Creating SSH key ..."
aws ec2 create-key-pair \
  --key-name $AWS_KEY_NAME \
  --query 'KeyMaterial' > ${AWS_KEY_NAME}.pem
state AWS_KEY_NAME
chmod 400 ${AWS_KEY_NAME}.pem

echo "Creating default security group ..."
readonly default_group_id=$(aws ec2 create-security-group \
  --group-name $AWS_DEFAULT_GROUP_NAME \
  --description $AWS_DEFAULT_GROUP_NAME \
  --vpc-id $vpc_id \
  --query 'GroupId'
)
state default_group_id
aws ec2 authorize-security-group-ingress \
  --group-id $default_group_id \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

echo "Creating manager security group ..."
readonly manager_group_id=$(aws ec2 create-security-group \
  --group-name $AWS_MANAGER_GROUP_NAME \
  --description $AWS_MANAGER_GROUP_NAME \
  --vpc-id $vpc_id \
  --query 'GroupId'
)
state manager_group_id
for port in 80 443
do
  aws ec2 authorize-security-group-ingress \
    --group-id $manager_group_id \
    --protocol tcp \
    --port $port \
    --cidr 0.0.0.0/0
done
for port in 5672 8101 53229
do
  aws ec2 authorize-security-group-ingress \
    --group-id $manager_group_id \
    --protocol tcp \
    --port $port \
    --source-group $default_group_id
done

echo "Creating manager instance ..."
# Fix for newer, backwards incompatible CentOS images
readonly cloudinit_file=$(mktemp)
cat <<EOF > $cloudinit_file
#!/bin/bash
sed -i -re 's/^verify=(platform_default|enable)/verify=disable/' \\
  /etc/python/cert-verification.cfg
EOF
readonly instance_id=$(aws ec2 run-instances \
  --image-id $AWS_AMI_ID \
  --count 1 \
  --instance-type $AWS_INSTANCE_TYPE \
  --key-name $AWS_KEY_NAME \
  --security-group-ids $default_group_id $manager_group_id \
  --subnet-id $subnet_id \
  --user-data file://$cloudinit_file \
  --block-device-mappings \
      'DeviceName=/dev/sda1,Ebs={VolumeSize=20,DeleteOnTermination=true}' \
  --query 'Instances[0].InstanceId'
)
state instance_id
aws ec2 wait instance-running --instance-ids $instance_id
readonly private_ip=$(aws ec2 describe-instances \
    --filters Name=instance-id,Values=$instance_id \
    --query 'Reservations[0].Instances[0].PrivateIpAddress' \
  | tr -d '"'
)
rm $cloudinit_file

echo "Adding elastic IP to manager ..."
readonly allocation_id=$(aws ec2 allocate-address \
  --domain vpc \
  --query 'AllocationId'
)
state allocation_id
readonly public_ip=$(aws ec2 describe-addresses \
    --filter Name=allocation-id,Values=$allocation_id \
    --query 'Addresses[0].PublicIp' \
  | tr -d '"'
)
aws ec2 associate-address \
  --instance-id $instance_id \
  --allocation-id $allocation_id &> /dev/null

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

if [[ $AWS_ACTIVATE_SWAP == "true" ]]
then
  echo "Activating swap on manager instance ..."
  sshi centos@$public_ip "sudo dd if=/dev/zero of=/swapfile bs=1MB count=6144"
  sshi centos@$public_ip "sudo chmod 0600 /swapfile"
  sshi centos@$public_ip "sudo mkswap /swapfile"
  sshi centos@$public_ip "sudo swapon /swapfile"
  sshi centos@$public_ip \
    "echo /swapfile none swap defaults 0 0 | sudo tee -a /etc/fstab"
fi

echo "Creating DICE plugin configuration ..."
cat <<EOF > dice-aws.yaml
aws:
  auth:
    aws_access_key_id: $AWS_ACCESS_KEY_ID
    aws_secret_access_key: $AWS_SECRET_ACCESS_KEY
    region_name: $AWS_DEFAULT_REGION
  env:
    vpc_id: $vpc_id
    subnet_id: $subnet_id
    key_name: $AWS_KEY_NAME
    default_security_group_id: $default_group_id
EOF

echo "Uploading DICE configuration to manager VM ..."
sshi centos@$public_ip "sudo mkdir /etc/dice"
scpi dice-aws.yaml ${AWS_KEY_NAME}.pem centos@$public_ip:.
sshi centos@$public_ip "sudo mv dice-aws.yaml /etc/dice/dice.yaml"
sshi centos@$public_ip "sudo chmod 444 /etc/dice/dice.yaml"
sshi centos@$public_ip "sudo mv ${AWS_KEY_NAME}.pem /root/.ssh/dice.key"
sshi centos@$public_ip "sudo chmod 400 /root/.ssh/dice.key"
rm dice-aws.yaml

echo "Creating bootstrap inputs template ..."
readonly cfy_admin_pass=$(openssl rand -base64 24 | tr "/+=" "_.-")
cat <<EOF > inputs.yaml
public_ip: $public_ip
private_ip: $private_ip
ssh_user: 'centos'
ssh_key_filename: $PWD/${AWS_KEY_NAME}.pem

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
  Manager VM private address: $private_ip
  SSH access to VM: ssh -i ${AWS_KEY_NAME}.pem centos@$public_ip
-----------------------------------------------------------------------------
EOF
