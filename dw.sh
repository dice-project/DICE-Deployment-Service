#!/bin/bash

set -e

for EXEC_ID in $(cfy executions list -d dice_deploy | grep started | awk '{print $2}') 
do
	cfy executions cancel --execution-id $EXEC_ID

	STATUS=$(cfy executions get -e $EXEC_ID | grep "| *$EXEC_ID" | awk '{print $6}')
	while [ "$STATUS" != "cancelled" ]
	do
		sleep 3
		STATUS=$(cfy executions get -e $EXEC_ID | grep "| *$EXEC_ID" | awk '{print $6}')
	done
done

cfy executions start -d dice_deploy -w uninstall
cfy deployments delete -d dice_deploy
cfy blueprints delete -b dice_deploy
