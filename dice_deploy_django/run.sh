#!/bin/bash

function run()
{
  # Start celery worker
  echo "Starting celery worker ..."
  celery -A dice_deploy worker --loglevel=info > celery.out 2> celery.err &
  local celery_pid=$!

  # Start server
  echo "Starting django server ..."
  python manage.py runserver 0.0.0.0:8080

  # Shutdown worker
  echo Cleaning up ...
  kill $celery_pid

  echo All done.
}

function reset()
{
  SUPERUSER_UNAME="${1-admin}"
  SUPERUSER_PASSWORD="${2-changeme}"
  SUPERUSER_EMAIL="${3-admin@example.com}"
  rm -rf db.sqlite3 uploads cfy_wrapper/migrations
  python manage.py makemigrations cfy_wrapper
  python manage.py migrate
  python manage.py create-dice-superuser \
    --username "${SUPERUSER_UNAME}" \
    --password "${SUPERUSER_PASSWORD}" \
    --email "${SUPERUSER_EMAIL}"
}

case $1 in
  reset)
    reset "$2" "$3" "$4"
    ;;

  *)
    run
    ;;
esac
