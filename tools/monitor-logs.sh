#!/bin/bash

# Iterate forever and slurp any new execution logs
# on the hard drive

function usage() {
    echo "Usage: $0 [ log_path | -h ]"
    echo ""
    echo "Runs in a loop and tails any execution logs that it "
    echo "encounters in status started, storing them into a file."
    echo "The logs are in a DEPLOYMENT_ID/EXECUTION_ID-WORKFLOW_ID.log file."
    echo ""
    echo "    log_path: path to where the tool creates the logs "
    echo "              (default: /tmp/cfy)"
    echo "    -h: print this usage"
    echo ""
}

function ensure_log_path() {
    mkdir -p "$1"
}

function run() {
    LOG_PATH="$1"
    local DEBUG_ON="" # "-vv"

    echo "Logging to $LOG_PATH"
    while [ 1 ]
    do
        local EXECUTIONS=$(cfy executions list | \
            grep started | \
            awk '{print $6 "+" $2 "+" $4}')

        for EXECUTION in $EXECUTIONS
        do
            TOKENS=$(echo "$EXECUTION" | \
                sed 's/+/ /g')
            EVENT_ID=$(echo "$TOKENS" | \
                awk '{print $2}')
            LOG=$(echo "$TOKENS" | \
                awk '{print $1 "/" $3 "-" $2 ".log"}')
            LOG="$LOG_PATH/$LOG"

            mkdir -p $(dirname $LOG)

            if [ ! -e "$LOG" ]
            then
                echo "starting $LOG"

                touch "$LOG"
                cfy events list -l $DEBUG_ON --tail -e $EVENT_ID > "$LOG" &
            fi
        done
        sleep 1
    done
}

if [ "$1" == "-h" ]
then
    usage
    exit 0
fi

LOG_PATH="${1:-/tmp/cfy}"

ensure_log_path "$LOG_PATH"
run "$LOG_PATH"
