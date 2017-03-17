#!/bin/bash

# A utility script for getting outputs from a given virtual deployment
# container and extracting a specific output's value

NAME="$0"

function usage () {
    cat << EOF

USAGE:
    $NAME CONTAINER_ID OUTPUT_NAME [ DDS_CONFIG_FILE ]

Prints the value of OUTPUT_NAME name from the outputs of the virtual
deployment container CONTAINER_ID to the standard output.

DDS_CONFIG_FILE is an optional parameter containing the path to the DICE
Deployment Service client's (CLI's) configuration, created by previously
running \`dice-deploy-cli use ...\` and \`dice-deploy-cli authenticate ...\` .
Default: \`.dds.conf\`

Please note that this script uses dice-deploy-cli and jq.

EOF
}

function check_args () {
    if [ "$#" != "2" ] && [ "$#" != "3" ]
    then
        echo "Wrong number of parameters: $#."
        usage
        exit 1
    fi
}

function main () {
    CONTAINER_ID="$1"
    OUTPUT_NAME="$2"

    # get outputs
    OUTPUTS=$(dice-deploy-cli --config "$CONFIG_FILE" outputs $CONTAINER_ID | \
        jq ".outputs[\"$OUTPUT_NAME\"].value")

    echo "$OUTPUTS"
}

CONFIG_FILE=${3:-.dds.conf}

check_args "$@"
main "$@"