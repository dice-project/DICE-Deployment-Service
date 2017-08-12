# Linux username for the CentOS
export CENTOS_USERNAME=centos

# Linux username for the Ubuntu
export UBUNTU_USERNAME=ubuntu

# Address of the VM containing the Cloudify Manager
export CFY_ADDRESS=10.10.43.156

# Port of the Cloudify Manager's web interface
export CFY_PORT=443

# E-mail address of the DICE Deployment Service administrator
export ADMIN_EMAIL=matej.artac@xlab.si

# Instance type ID for a small server. openstack flavor list
export SMALL_INSTANCE_ID=627144d1-cad6-4511-b192-4b24a56eb6ee

# Instance type ID for a medium server
export MEDIUM_INSTANCE_ID=93e4960e-9b6d-454f-b422-0d50121b01c6

# Instance type ID for a large server
export LARGE_INSTANCE_ID=30734cac-0a4e-4487-94e7-fd44d82027a1

# ID of an image with Ubuntu 14.04. openstack image list
export UBUNTU_IMAGE_UUID=ca290f2d-5163-483b-9dd5-fafe21517c0a

# ID of an image with CentOS 7. openstack image list
export CENTOS_IMAGE_UUID=9ea4856a-32b2-4553-b408-cfa4cb1bb40b

# Should the debug mode for the DICE Deployment Service be enabled?
export DDS_ENABLE_DEBUG=false

# Target platform
export DEPLOYMENT_PLATFORM=openstack

# values not needed
export FCO_SMALL_DISK_UUID=dummy
export FCO_MEDIUM_DISK_UUID=dummy
export FCO_LARGE_DISK_UUID=dummy
