#!/bin/sh

# This file expects that proper environment has been set up before being run.
# Requirements:
#   - cfy command line program
#   - requests python package
#   - cloudify_rest_client python package
#
# This can be achieved by simply running
#
#   virtualenv venv && . venv/bin/activate && pip install cloudify==3.x


# Create temporary file for communication between processes.
TMP_FILE=$(mktemp)

# Bootstrap dice deployment service
python bootstrap.py $TMP_FILE
BOOTSTRAP_STATUS=$?

if [ "x$BOOTSTRAP_STATUS" = "x0" ]
then
  source $TMP_FILE
  python -m unittest discover
  TEST_STATUS=$?
fi

if [ "x$BOOTSTRAP_STATUS" != "x3" ]
then
  python teardown.py $TMP_FILE
  TEARDOWN_STATUS=$?
fi

# Remove temporary file
rm $TMP_FILE

# Ugly as heck, but we want to sh-compatible
[ "x$BOOTSTRAP_STATUS" = "x0" ] || exit 1
[ "x$TEST_STATUS"      = "x0" ] || exit 1
[ "x$TEARDOWN_STATUS"  = "x0" ] || exit 1

exit 0
