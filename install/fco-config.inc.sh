# UUID of the VDC. See "Information" tab of an existing Server
export FCO_VDC_UUID=42bb54ac-4090-3caa-b730-e916b27daeff

# UUID of the Network. See "Information" tab of an existing Server, open its
#     NIC, see "Information" tab and look for "Network"
export FCO_NETWORK_UUID=179a6319-3a74-3942-a59c-742d5eab43fe

# Offer that should be used to create server
export FCO_DISK_OFFER_UUID=0b54fac2-ce18-3b93-8285-5c827c00cf35
export FCO_SERVER_OFFER_UUID=bcdbb396-6121-37c8-81ad-37b59a7b92e7

# CentOS image UUID.
export FCO_IMAGE_UUID=00468b94-e602-3b96-9651-f430bec50f3a

# Name of the SSH key pair that will be installed on all VMs when Cloudify
# creates them.
export FCO_KEY_NAME=cfy-key

# Name of the Cloudify Manager server.
export FCO_SERVER_NAME=cfy-manager

# Firewall template name for Cloudify Manager.
export FCO_MANAGER_TEMPLATE_NAME=cfy-manager-secgrp

# If the instance type has less than 8 GB of RAM, set this to true. If the
# instance is large enough, set this to false.
export FCO_ACTIVATE_SWAP=false
