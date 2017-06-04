# IP address range that will be used by subnet that all VMs will be part of.
export AWS_SUBNET_CIDR=10.50.51.0/24

# Name of the SSH key pair that will be installed on all VMs when Cloudify
# creates them.
export AWS_KEY_NAME=cloudify-manager-key

# Default security group name that will be installed on all VMs when Cloudify
# creates new VM.
export AWS_MANAGER_GROUP_NAME=cloudify-manager-grp

# Name of the security group that will contain firewall rules that will allow
# access to the manager.
export AWS_DEFAULT_GROUP_NAME=cloudify-default-grp

# CentOS 7 AMI. YOu can get the latest available AMI ID using this command:
# aws ec2 describe-images \
#     --owners aws-marketplace \
#     --filters Name=product-code,Values=aw0evgkw8e5c1q413zgy5pjce \
#               Name=architecture,Values=x86_64 \
#   | jq -r '.Images | sort_by(.CreationDate) | .[-1].ImageId')
export AWS_AMI_ID=ami-061b1560

# Instance type that will host Cloudify Manager. This should have at least
# 4 GB of RAM available.
export AWS_INSTANCE_TYPE=m3.medium

# Amazon credentials.
export AWS_DEFAULT_REGION=eu-west-1
export AWS_ACCESS_KEY_ID="AWS access key"
export AWS_SECRET_ACCESS_KEY="AWS secret access key"

# If the instance type has less than 8 GB of RAM, set this to true. If the
# instance is large enough, set this to false.
export AWS_ACTIVATE_SWAP=false
