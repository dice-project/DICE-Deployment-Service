#!/bin/bash

set -e

DEPLOY_NAME=${1:-dice_deploy}

for EXEC_ID in $(cfy executions list -d $DEPLOY_NAME | grep started | awk '{print $2}')
do
	cfy executions cancel --execution-id $EXEC_ID

	STATUS=$(cfy executions get -e $EXEC_ID | grep "| *$EXEC_ID" | awk '{print $6}')
	while [ "$STATUS" != "cancelled" ]
	do
		sleep 3
		STATUS=$(cfy executions get -e $EXEC_ID | grep "| *$EXEC_ID" | awk '{print $6}')
	done
done

set +e

cfy executions start -d $DEPLOY_NAME -w uninstall
cfy deployments delete -d $DEPLOY_NAME
cfy blueprints delete -b $DEPLOY_NAME
