#!/bin/bash

IN_MODEL="$(realpath $1)"
DEPLOYER_URL="$2"
DEPLOYER_USERNAME="$3"
DEPLOYER_PASSWORD="$4"
CONTAINER="$5"

BLUEPRINT="$IN_MODEL.yaml"

dicer_xmi2tosca.sh "$IN_MODEL" "$IN_MODEL"

dice-deploy-cli use "$DEPLOYER_URL"
dice-deploy-cli authenticate "$DEPLOYER_USERNAME" "$DEPLOYER_PASSWORD"
dice-deploy-cli deploy $CONTAINER $BLUEPRINT

dice-deploy-cli wait-deploy $CONTAINER

dice-deploy-cli outputs $CONTAINER
