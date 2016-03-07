#!/bin/bash

function run()
{
  # Start celery worker
  echo "Starting celery worker ..."
  celery -A dice_deploy worker --loglevel=info > celery.out 2> celery.err &
  local celery_pid=$!

  # Start server
  echo "Starting django server ..."
  ./manage.py runserver 0.0.0.0:8080

  # Shutdown worker
  echo Cleaning up ...
  kill $celery_pid

  echo All done.
}

function reset()
{
  rm -rf db.sqlite3 uploads cfy_wrapper/migrations
  ./manage.py makemigrations cfy_wrapper
  ./manage.py migrate
}

case $1 in
  reset)
    reset
    ;;

  *)
    run
    ;;
esac
