#!/bin/bash

function usage() {
    cat <<EOF

    Usage:
        $0 BLUEPRINT_PATH RESOURCES_PATH DEPLOYER_URL \\
           USERNAME PASSWORD CONTAINER
        $0 project.dice-delivery

    Automates connecting to the deployment service and deploying of the
    application blueprint.

    Accepts either individual parameters in the command line or a project
    file containing the same parameters.

        BLUEPRINT_PATH - path to the TOSCA yaml blueprint
        RESOURCES_PATH - path to the folder containing resources to be
                         bundled with the blueprint
        DEPLOYER_URL -   URL of the deployment service
        USERNAME -       user name part of the credentials to the
                         deployment service
        PASSWORD -       password name part of the credentials to the
                         deployment service
        CONTAINER -      UUID of the container to deploy into
        BIN_PATH -       output path to where the blueprint package will
                         be created; default value: bin

    project.dice-delivery - name of the file containing the values of the
                         parameters listed above. An example configuration
                         is as follows:

    BLUEPRINT_PATH=model/spark-openstack.yaml
    RESOURCES_PATH=resources
    DEPLOYER_URL=http://10.10.43.22/
    USERNAME=admin
    PASSWORD=passvv0rd
    CONTAINER=6681034c-3419-4da0-91b3-aa4f481f29df

EOF
}

function package() {
    local BLUEPRINT_PATH="$1"
    local RESOURCES_PATH="$2"
    local BIN_PATH="$3"

    mkdir -p "$BIN_PATH"

    local T=$(mktemp -d)
    chmod 755 $T

    cp "$BLUEPRINT_PATH" "$T/blueprint.yaml"
    cp -r "$RESOURCES_PATH" $T
    tar -cvzf "$BIN_PATH/blueprint.tar.gz" -C $(dirname $T) $(basename $T)
    rm -rf $T
}

function check_blueprint_contents() {
    if [[ ! -f $1 ]]
    then
        echo "Blueprint file '$1' does not exist."
        exit 1
    fi
    if [[ ! -d $2 ]]
    then
        echo "Resource folder '$2' does not exist."
        exit 1
    fi
}

function deploy() {
    local BLUEPRINT_PATH="$1"
    local RESOURCES_PATH="$2"
    local DEPLOYER_URL="$3"
    local USERNAME="$4"
    local PASSWORD="$5"
    local CONTAINER="$6"
    local BIN_PATH="${7-bin}"

    check_blueprint_contents "$BLUEPRINT_PATH" "$RESOURCES_PATH"
    package "$BLUEPRINT_PATH" "$RESOURCES_PATH" "$BIN_PATH"

    set -e

    dice-deploy-cli use "$DEPLOYER_URL"
    dice-deploy-cli authenticate "$USERNAME" "$PASSWORD"
    dice-deploy-cli deploy $CONTAINER "$BIN_PATH/blueprint.tar.gz"
    dice-deploy-cli wait-deploy $CONTAINER

    dice-deploy-cli outputs $CONTAINER
}

function deploy_from_project() {
    # Declarations
    PROJECT_PATH=$(realpath "$1")
    PROJECT_FOLDER=$(dirname $PROJECT_PATH)
    if [ ! -f "$PROJECT_PATH" ]
    then
        echo "$1 not found"
        exit 2
    fi
    BIN_PATH="$PROJECT_FOLDER/bin"

    echo "to be deployed ... data in $PROJECT_PATH"

    # Collect parameters from the project file
    local varnames="BLUEPRINT_PATH RESOURCES_PATH DEPLOYER_URL USERNAME PASSWORD CONTAINER"
    local -A params

    for var in $varnames
    do
        params[$var]=$(grep -Po "(?<=^${var}=).+$" "$PROJECT_PATH")

        if [ "$?" != "0" ]
        then
            echo "Missing parameter: $var"
            exit 3
        fi
    done

    deploy "$PROJECT_FOLDER/${params[BLUEPRINT_PATH]}" \
         "$PROJECT_FOLDER/${params[RESOURCES_PATH]}" \
         "${params[DEPLOYER_URL]}" \
         "${params[USERNAME]}" \
         "${params[PASSWORD]}" \
         "${params[CONTAINER]}" \
         "$PROJECT_FOLDER/bin"
}

function handle_single_parameter() {
    case "$1" in
        "-h"|"--help")
            usage
            ;;
        *)
            deploy_from_project "$1"
            ;;
    esac
}

case "$#" in
    "1")
        handle_single_parameter "$1"
        ;;
    "6")
        deploy "$@"
        ;;
    "7")
        deploy "$@"
        ;;
    *)
        usage
        exit 1
        ;;
esac
