# Managing server certificates

This document demonstrates some of the procedures that may be useful for
system administrators who are going to install DICE related services as well
as end users that will consume DICE services through clients, provided by DICE
project.


## Administrators

This section contains instructions on how to create self-signed certificates
that can be used when deploying Cloudify Manager and DICE Deployment Service.


### Creating self-signed certificates

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
        -days 730 -out server.crt -keyout server.key

Newly created key can be found in `server.key` file and server certificate in
`server.crt`. These two files can be used to setup the server.


## End user tasks

As users, we need to be able to configure our clients with proper certificates
in order to establish secure connection to the service. Instructions in this
section show how to obtain server certificate using command line tools and how
to create key store that can be used by IDE plugin.


### Downloading server certificate

There are at least three ways of obtaining server certificate:

 1. Administrator that installed the server sent us the certificate (safe
    option).
 2. Visit server using browser and export certificate.
 3. Use OpenSSL to download certificate.

We will only look at third option, since first two should not pose too much of
a challenge. And even third options is done using single command:

    $ openssl s_client -connect server-ip:443 < /dev/null 2> /dev/null \
        | openssl x509 -out server-name.crt


### Importing certificate into key store

Now that we have our server certificate, we can import it into Java key store.
For starters, we need to execute:

    $ keytool -importcert -v -trustcacerts -file server-name.crt -alias cfy \
        -keystore local.jks

This command will prompt us for key store password and if we trust the
certificate that is being imported. After all this is done, we are ready to
use this key store with IDE plugin.
