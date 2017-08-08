# Linux username for the CentOS
export CENTOS_USERNAME=centos

# Address of the VM to contain the Cloudify Manager
export CFY_ADDRESS=109.231.122.170

# Port of the Cloudify Manager's web interface
export CFY_PORT=443

# Customer UUID. See "Information" tab of an existing Server
export FCO_CUSTOMER_UUID=e50bfd1b-253a-3290-85ff-95e218398b7e

# User account (or API key) UUID for the FCO account. See "Information" tab of
#     the User
export FCO_USER_UUID=089e2a3a-5ae9-34e4-b03c-c694268acf1c

# User account password for the FCO account
export FCO_PASSWORD="Secret password for FCO"

# UUID of the VDC. See "Information" tab of an existing Server
export FCO_VDC_UUID=42bb54ac-4090-3caa-b730-e916b27daeff

# UUID of the Network. See "Information" tab of an existing Server, open its
#     NIC, see "Information" tab and look for "Network"
export FCO_NETWORK_UUID=179a6319-3a74-3942-a59c-742d5eab43fe

# Path to the SSH private key that will be used by the Cloudify Manager
export CFY_AGENT_SSH_KEY_PATH=cfy-agent

# SSH key ID of the keypair that will be used by the Cloudify Manager
export CFY_AGENT_KEY_UUID=21e90e22-31c6-3d64-8590-af03dea25392

# Path to the SSH private key that we can use to connect to Cloudify Manager VM
export CFY_MANAGER_SSH_KEY_PATH=cfy-manager.pem

# If the instance type has less than 8 GB of RAM, set this to true. If the
# instance is large enough, set this to false.
export FCO_ACTIVATE_SWAP=false
