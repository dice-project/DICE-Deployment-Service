# Setting up Cloudify manager on OpenStack

In this document we will describe specifics of bootstrap procedure for Cloudify
3.3.1 on OpenStack. The document is based on the
[official instructions](#official-documentation), providing additional information about
how to obtain the needed parameters.


## Preparing environment

First we need to install prerequisites for Cloudify's CLI client. For
Redhat related GNU/Linux distributions, following packages need to be
installed: `python-virtualenv` and `python-devel`. Adjust properly for
Ubuntu and the like.

Now create new folder, create new python virtual environment and install
`cloudify` package.

    $ mkdir -p ~/dice && cd ~/dice
    $ virtualenv venv
    $ . venv/bin/activate
    $ pip install cloudify==3.3.1

We can move to the bootstrap procedure now.


## Preparing inputs

First, we need to obtain official blueprints for manager.

    $ git clone https://github.com/cloudify-cosmo/cloudify-manager-blueprints
    $ git checkout -b v3.3.1 tags/3.3.1

Open `openstack-manager-blueprint-inputs.yaml` file and fill in first half of
the file. Modified file should look something like this:

    keystone_username:       '<user_name>'
    keystone_password:       '<pass>'
    keystone_tenant_name:    'dice'
    keystone_url:            '<keystone_url>'
    manager_public_key_name: '<manager_public_key_name>'
    agent_public_key_name: '<agent_public_key_name>'
    image_id: '<image_id>'
    flavor_id: '<flavor_id>'
    external_network_name: '<external-network-name>'
    use_existing_manager_keypair: false
    use_existing_agent_keypair: false
    manager_server_name: <manager_server_name>
    manager_server_user: ubuntu
    manager_private_key_path: <local path to manager private key>
    agent_private_key_path: <local path to agent private key>
    agents_user: ubuntu
    management_network_name: <management_network_name>
    management_subnet_name: <management_subnet_name>
    management_router: <management_router>
    manager_security_group_name: <manager_security_group_name>
    agents_security_group_name: <agents_security_group_name>
    manager_port_name: <manager_port_name>
    manager_volume_name: <manager_volume_name>
    nova_url: ''
    neutron_url: ''
    resources_prefix: 'cfy-'

Make sure you replace `<user_name>` and `<pass>` fields with your own
credentials.

To get `keystone_tenant_name`, login to OpenStack dashboard and take
note of current project name. That one was easy.

To get our hands on `keystone_url`, we need to navigate to 
`Access & Security -> API Access`. Required url is listed in _Identity_ table
row.

Getting `image_id` and `flavor_id` values requires a bit more work,
since OpenStack dashboard does nor expose those two. First, we need to
install `python-nova` package (adjust for Ubuntu). Now we can list all
available images by executing

    $ nova --os-username user_name --os-tenant-name dice \
        --os-auth-url 'http://172.16.93.211:5000/v2.0' image-list

This should return table, similar to this:

    +-----------------------------+----------------+--------+--------+
    | ID                          | Name           | Status | Server |
    +-----------------------------+----------------+--------+--------+
    | bd632c08-fe42-4ecc-8746-074 | Ubuntu 12.04   | ACTIVE |        |
    | 98eedeb3-f027-4583-b870-a9e | Ubuntu 14.04   | ACTIVE |        |
    | 36dbc4e8-81dd-49f5-9e43-f4a | Ubuntu 14.04.3 | ACTIVE |        |
    +-----------------------------+----------------+--------+--------+

Now simply select proper image and take note of it's `ID` field.

Getting flavor id is done similarly. Execute

    $ nova --os-username user_name --os-tenant-name dice \
        --os-auth-url 'http://172.16.93.211:5000/v2.0' flavor-list

Now select `ID` from table, that should look something like this (some
columns in next output listing are left out to reduce clutter):

    +----------------------------+-----------------+-----------+------+
    | ID                         | Name            | Memory_MB | Disk |
    +----------------------------+-----------------+-----------+------+
    | 070005dc-9bd5-4c0c-b2c6-88 | 512MB-1CPU-10GB | 512       | 10   |
    | 0ff7f971-d421-4fa2-b9db-95 | 512MB-1CPU-0GB  | 512       | 0    |
    | 1bd34fe1-57b3-4937-bf60-5e | 4GB-2CPU-10GB   | 4096      | 10   |
    | 3494a89a-3574-40a8-91c6-49 | 8GB-4CPU-10GB   | 8192      | 10   |
    | 45170672-5608-473e-af9c-90 | 2GB-2CPU-10GB   | 2048      | 10   |
    +----------------------------+-----------------+-----------+------+

The Cloudify Manager blueprint for OpenStack currently assumes that the subnet
CIDR to be used both for the Cloudify Manager and the VMs that Cloudify will
be creating during its operation.

Another thing to keep in mind is that the following fields need to be unique
in OpenStack installation:

  * manager_public_key_name
  * agent_public_key_name
  * manager_server_name
  * management_network_name
  * management_subnet_name
  * management_router
  * manager_security_group_name
  * agents_security_name
  * manager_volume_name

If we follow the naming scheme in the example, chances of name collision are
negligible. But still, if one encounters an error similar to the one below,
double check your name uniqueness.

    Workflow failed: Task failed 'nova_plugin.server.create' ->
    Expected exactly one object of type network with match
    {'name': u'cloudify-management-network'} but there are 2

As for the manager and agent keys, make sure path to the key is absolute that
files do not exist already or the bootstrap process will fail.


## Executing bootstrap

First, we need to create initial folder structure for bootstrap process.
Running `cfy init` will take care of that. After this is done, we can
finally bootstrap the manager by executing

    $ cfy bootstrap --install-plugins -p \
      openstack-manager-blueprint.yaml \
      -i openstack-manager-blueprint-inputs.yaml


## Removing installation

Simply execute `cfy teardown -f`. This will remove all traces of cloudify
manager from openstack.

# Official documentation

For further reference, the following links point to the official documentation:

* [How to bootstrap Cloudify Manager v.3.3.1](http://docs.getcloudify.org/3.3.1/manager/bootstrapping/)
* [OpenStack bootstrap reference v.3.3.1](http://docs.getcloudify.org/3.3.1/manager/bootstrap-reference-openstack/)