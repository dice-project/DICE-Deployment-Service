# Existing external network name, used to access the web.
export OS_EXTERNAL_NETWORK_NAME=xlab

# Network, subnet and router configuration.
export OS_NETWORK_NAME=cfy-network
export OS_SUBNET_NAME=cfy-subnet
export OS_SUBNET_CIDR=10.50.51.0/24
export OS_DNS1=172.16.0.10
export OS_DNS2=172.16.0.11
export OS_ROUTER_NAME=cfy-router

# Name of the SSH key pair that will be installed on all VMs when Cloudify
# creates them.
export OS_KEY_NAME=cfy-key

# Security groups that script will create. OS_DEFAULT_GROUP_NAME will be added
# to any instance that will be launched by Cloudify. OS_MANAGER_GROUP_NAME
# will be attached to manager instance and will contain rules needed by
# manager.
export OS_DEFAULT_GROUP_NAME=cfy-default-secgrp
export OS_MANAGER_GROUP_NAME=cfy-manager-secgrp

# Manager server properties.
export OS_SERVER_NAME=cfy-server
export OS_IMAGE_ID=840a776a-f077-4360-a6ef-a5a90ca3cdf9
export OS_FLAVOR_ID=93e4960e-9b6d-454f-b422-0d50121b01c6

# If the instance type has less than 8 GB of RAM, set this to true. If the
# instance is large enough, set this to false.
export OS_ACTIVATE_SWAP=true
