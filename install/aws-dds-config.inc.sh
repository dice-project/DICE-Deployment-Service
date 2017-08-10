# Linux username for the CentOS
export CENTOS_USERNAME=centos

# Linux username for the Ubuntu
export UBUNTU_USERNAME=ubuntu

# Address of the VM containing the Cloudify Manager
export CFY_ADDRESS=52.16.189.169

# Port of the Cloudify Manager's web interface
export CFY_PORT=443

# E-mail address of the DICE Deployment Service administrator
export ADMIN_EMAIL=matej.artac@xlab.si

# Instance type for a small server. Refer to
# https://aws.amazon.com/ec2/instance-types/
export SMALL_INSTANCE_ID=m3.medium

# Instance type for a medium server
export MEDIUM_INSTANCE_ID=m3.medium

# Product offer UUID for a large flavoured server
export LARGE_INSTANCE_ID=m3.large

# AMI of the Ubuntu 14.04 OS image. Use Ubuntu AMI locator:
# https://cloud-images.ubuntu.com/locator/ec2/
export UBUNTU_IMAGE_UUID=ami-09447c6f

# AMI of the CentOS 7 OS image. AMI codes for CentOS available at:
# https://wiki.centos.org/Cloud/AWS
# You can get the latest available AMI ID using
# this command:
# aws ec2 describe-images \
#     --owners aws-marketplace \
#     --filters Name=product-code,Values=aw0evgkw8e5c1q413zgy5pjce \
#               Name=architecture,Values=x86_64 \
#   | jq -r '.Images | sort_by(.CreationDate) | .[-1].ImageId')
export CENTOS_IMAGE_UUID=ami-061b1560

# Should the debug mode for the DICE Deployment Service be enabled?
export DDS_ENABLE_DEBUG=false

# Target platform
export DEPLOYMENT_PLATFORM=aws

# values not needed
export FCO_SMALL_DISK_UUID=dummy
export FCO_MEDIUM_DISK_UUID=dummy
export FCO_LARGE_DISK_UUID=dummy
