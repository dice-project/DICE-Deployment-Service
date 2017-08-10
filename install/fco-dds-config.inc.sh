# Linux username for the CentOS
export CENTOS_USERNAME=centos

# Linux username for the Ubuntu
export UBUNTU_USERNAME=ubuntu

# Address of the VM containing the Cloudify Manager
export CFY_ADDRESS=$CFY_ADDRESS

# Port of the Cloudify Manager's web interface
export CFY_PORT=443

# E-mail address of the DICE Deployment Service administrator
export ADMIN_EMAIL=matej.artac@xlab.si

# UUID of the product offer for disk of small size. Look for the "Disk" entry in
# the Server's "Information" tab and click the link (either the name or the
# UUID) of the disk. Then switch to "Information" tab and look for the Product
# offer's UUID.
export FCO_SMALL_DISK_UUID=fa2c28ec-3835-3006-a64a-fd78252e14ad

# UUID of the product offer for disk of medium size
export FCO_MEDIUM_DISK_UUID=fa2c28ec-3835-3006-a64a-fd78252e14ad

# UUID of the product offer for disk of large size
export FCO_LARGE_DISK_UUID=fa2c28ec-3835-3006-a64a-fd78252e14ad

# Product offer UUID for a small flavoured server. In the Server page's
# "Information" tab, look for the "UUID" column of the Product offer row.
export SMALL_INSTANCE_ID=65ea40ab-d96f-3d7c-84a0-cf6dd6ee9c67

# Product offer UUID for a medium flavoured server
export MEDIUM_INSTANCE_ID=7210fc69-f50f-3150-9aa8-a7ea5fdb8691

# Product offer UUID for a large flavoured server
export LARGE_INSTANCE_ID=bcdbb396-6121-37c8-81ad-37b59a7b92e7

# Image UUID of the Ubuntu 14.04 OS image. In the "Information" tab of the
# disk's details, look for the row with item Image. Check the "Name" value, and
# if it is one of the Ubuntu 14.04, then note down the "UUID" value.
export UBUNTU_IMAGE_UUID=03e7505d-1616-339f-951e-d6e815b940da

# Image UUID of the CentOS 7 OS image
export CENTOS_IMAGE_UUID=00468b94-e602-3b96-9651-f430bec50f3a

# Should the debug mode for the DICE Deployment Service be enabled?
export DDS_ENABLE_DEBUG=false

# Platform
export DEPLOYMENT_PLATFORM=fco
