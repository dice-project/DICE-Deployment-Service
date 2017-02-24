# Setting up Cloudify manager on OpenStack

In this document we will describe specifics of bootstrap procedure for Cloudify
3.4.1 on OpenStack. The document is based on the
[official instructions](#official-documentation), updated with instructions
on how to use latest OpenStack plugin to bootstrap it.


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
    $ pip install cloudify==3.4.1

This being out of the way, we can now install required python packages.
But first, we need to obtain official blueprints for manager.

    $ git clone --depth 1 --branch feature/ssl \
        https://github.com/xlab-si/cloudify-manager-blueprints.git
    $ cd cloudify-manager-blueprints

With blueprints present locally, we can install dependencies that are required
by manager blueprint. We do this by executing

    $ cfy init
    $ cfy local install-plugins -p openstack-manager-blueprint.yaml

Now we need to get our OpenStack credentials. Navigate to your OpenStack
dashboard and click "Access & security", "API Access" and then download
OpenStack RC file. We will assume here that the file has been downloaded to
`~/dice/os-rc.sh`. Next, we need to source this file by running

    $ . ~/dice/os-rc.sh

In order to prevent `requests` experiencing a fit when confronted with some
certificates, we reinstall them using `security` flag:

    $ pip install -U requests[security]

That last command completes our environment setup. Now we must prepare
inputs that will be used by bootstrap process.


## Preparing inputs

Checked out repository contains a special helper script that serves two
purposes:

 1. It tests whether python clients support our OpenStack installation and
 2. it makes it a breeze to prepare inputs.

Usage is really simple. Just execute

    $ ./create-openstack-inputs.py > os-inputs.yaml

and follow the instructions. Just make sure you use CentOS image when asked
about image and make sure that flavor that you use has at least 5 GB of RAM
and at least 2 CPUs. Another thing that can cause troubles down the road are
non-unique names of various resources. This is problematic only if you have
multiple cloudify installations being hosted on the same OpenStack
installation. The input preparation script asks about prefix that can be used
to avoid name collisions. Default prefix is set to `cfy-`, but you can change
it to just about anything.

When the script terminates, `os-inputs.yaml` file will contain data that can
be used to bootstrap manager.

In order to fortify installation, we will set some security inputs for
Cloudify manager. This is achieved by adding the following lines to
`os-inputs.yaml` file:

    security_enabled: true
    ssl_enabled: true
    admin_username: admin
    admin_password: ADMIN_PASS
    rabbitmq_username: cloudify
    rabbitmq_password: RABBIT_PASS

Replace `ADMIN_PASS` and `RABBIT_PASS` placeholders with secure passwords.
**WARNING:** Current version of Cloudify agent that gets installed on manager
has a bug that prevents connecting to RabbitMQ if `rabbitmq_username`or
`rabbitmq_password` contains characters that need to be escaped when used in
URLs. Bug has been fixed, but current version does not have it applied yet. In
the mean time, use longer username and password that match regular expression
`[A-Za-z0-9_.-~]+`.

Next, we must create floating IP for the server.


## Creating floating IP for manager

Since our goal is to access Cloudify Manager over https, we need to create
floating IP address beforehand. This way we will be able to generate server
key and certificate that we will pass to bootstrap procedure.

Creating floating IP can be done via OpenStack web interface, but its id still
needs to be retrieved using command line tools. In this guide, we will create
floating IP using neutron.

    $ neutron floatingip-create NETWORK
    Created a new floatingip:
    +---------------------+--------------------------------------+
    | Field               | Value                                |
    +---------------------+--------------------------------------+
    | description         |                                      |
    | dns_domain          |                                      |
    | dns_name            |                                      |
    | fixed_ip_address    |                                      |
    | floating_ip_address | 10.10.43.132                         |
    | floating_network_id | 753940e0-c2a7-4c9d-992e-4d5bd71f85aa |
    | id                  | e2f2955f-cdd8-4cd7-a73a-ade4c79a6a69 |
    | port_id             |                                      |
    | router_id           |                                      |
    | status              | DOWN                                 |
    | tenant_id           | b478d718d45d4831a2a85f48cdfa1899     |
    +---------------------+--------------------------------------+

Replace `NETWORK` in the command above with the name of the network you
selected when creating inputs. To make manager actually use this floating IP,
we need to append the following line to the inputs:

    manager_floating_ip_id: e2f2955f-cdd8-4cd7-a73a-ade4c79a6a69

Now we need to create server key and certificate.


## Creating server certificate

Creating self signed certificate that everyone is happy with is a bit of an
art, but the instructions that follow should make this process relatively
pain-free.

First, we need to create openssl configuration that will be used to create key
and certificate. Simply copy the configuration pasted below into file
`ssl.cnf` and then edit the final part, marked with comment. Make sure you
replace IP address with address of the floating IP we just created.

    HOME = .
    RANDFILE = $ENV::HOME/.rnd
    oid_section = new_oids
    
    [ new_oids ]
    tsa_policy1 = 1.2.3.4.1
    tsa_policy2 = 1.2.3.4.5.6
    tsa_policy3 = 1.2.3.4.5.7
    
    [ ca ]
    default_ca = CA_default
    
    [ CA_default ]
    dir = ./diceCA
    certs = $dir/certs
    crl_dir = $dir/crl
    database = $dir/index.txt
    new_certs_dir = $dir/newcerts
    certificate = $dir/cacert.pem
    serial = $dir/serial
    crlnumber = $dir/crlnumber
    crl = $dir/crl.pem
    private_key = $dir/private/cakey.pem# The private key
    RANDFILE = $dir/private/.rand
    x509_extensions = usr_cert
    name_opt = ca_default
    cert_opt = ca_default
    default_days = 365
    default_crl_days= 30
    default_md = default
    preserve = no
    policy = policy_match
    
    [ policy_match ]
    countryName = match
    stateOrProvinceName = match
    organizationName = match
    organizationalUnitName = optional
    commonName = supplied
    emailAddress = optional
    
    [ req ]
    default_bits = 2048
    default_keyfile = privkey.pem
    distinguished_name = req_distinguished_name
    attributes = req_attributes
    x509_extensions = v3_ca
    prompt = no
    string_mask = utf8only
    
    [ req_attributes ]
    challengePassword = A challenge password
    challengePassword_min = 4
    challengePassword_max = 20
    unstructuredName = An optional company name
    
    [ usr_cert ]
    basicConstraints=CA:FALSE
    nsComment = "OpenSSL Generated Certificate"
    subjectKeyIdentifier=hash
    authorityKeyIdentifier=keyid,issuer
    
    [ v3_req ]
    basicConstraints = CA:FALSE
    keyUsage = nonRepudiation, digitalSignature, keyEncipherment
    
    [ v3_ca ]
    subjectAltName = @alternate_names
    subjectKeyIdentifier=hash
    authorityKeyIdentifier=keyid:always,issuer
    basicConstraints = CA:true
    
    [ crl_ext ]
    authorityKeyIdentifier=keyid:always
    
    [ proxy_cert_ext ]
    basicConstraints=CA:FALSE
    nsComment = "OpenSSL Generated Certificate"
    subjectKeyIdentifier=hash
    authorityKeyIdentifier=keyid,issuer
    proxyCertInfo=critical,language:id-ppl-anyLanguage,pathlen:3,policy:foo
    
    [ tsa ]
    default_tsa = tsa_config1
    
    [ tsa_config1 ]
    dir = ./diceCA
    serial = $dir/tsaserial
    crypto_device = builtin
    signer_cert = $dir/tsacert.pem
    certs = $dir/cacert.pem
    signer_key = $dir/private/tsakey.pem
    default_policy = tsa_policy1
    other_policies = tsa_policy2, tsa_policy3
    digests = sha256, sha384, sha512
    accuracy = secs:1, millisecs:500, microsecs:100
    clock_precision_digits = 0
    ordering = yes
    tsa_name = yes
    ess_cert_id_chain = no
    
    # Modifications are done below this comment
    [ alternate_names ]
    IP.1 = 10.10.43.13
    
    [ req_distinguished_name ]
    countryName = SI
    stateOrProvinceName = Slovenia
    localityName = Ljubljana
    0.organizationName = XLAB d.o.o.
    organizationalUnitName = Research
    commonName = XLAB
    emailAddress = tadej.borovsak@xlab.si

Generating certificate is now as easy as calling

    $ openssl req -new -nodes -x509 -newkey rsa:2048 -sha256 -config ssl.cnf \
        -out resources/ssl/server.crt -days 730 \
        -keyout resources/ssl/server.key

Now we can proceed to actually executing bootstrap procedure.


## Executing bootstrap

First, we need to create initial folder structure for bootstrap process.
Running `cfy init` will take care of that. After this is done, we can
finally bootstrap the manager by executing

    $ export CLOUDIFY_USERNAME=admin
    $ export CLOUDIFY_PASSWORD=ADMIN_PASS
    $ export CLOUDIFY_SSL_CERT="$PWD/resources/ssl/server.crt"
    $ cfy bootstrap -p openstack-manager-blueprint.yaml -i os-inputs.yaml
    $ cfy status


## Removing installation

Simply execute `cfy teardown -f`. This will remove all traces of Cloudify
manager from OpenStack.

# Official documentation

For further reference, the following links point to the official documentation:

* [How to bootstrap Cloudify Manager v.3.4.1](http://docs.getcloudify.org/3.4.1/manager/bootstrapping/)
* [OpenStack bootstrap reference v.3.4.1](http://docs.getcloudify.org/3.4.1/manager/bootstrap-reference-openstack/)
