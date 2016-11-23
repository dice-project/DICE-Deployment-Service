#!/bin/bash

function run()
{
  # Start celery worker
  echo "Starting celery worker ..."
  celery worker -A dice_deploy -Q dice_deploy -l debug --without-gossip \
    --without-mingle --purge > celery-out.log 2> celery-err.log &
  local celery_pid=$!

  # Start celery flower
  celery flower --port=5555 > flower-out.log 2> flower-err.log &
  local flower_pid=$!

  # Start server
  echo "Starting django server ..."
  python manage.py runserver 0.0.0.0:8080

  # Shutdown flower and worker
  echo Cleaning up ...
  kill $flower_pid
  kill $celery_pid

  echo All done.
}

function reset()
{
  SUPERUSER_UNAME="${1:-admin}"
  SUPERUSER_PASSWORD="${2:-changeme}"
  SUPERUSER_EMAIL="${3:-admin@example.com}"
  rm -rf db.sqlite3 uploads cfy_wrapper/migrations
  python manage.py makemigrations cfy_wrapper
  python manage.py migrate
  python manage.py create-dice-superuser \
    --username "${SUPERUSER_UNAME}" \
    --password "${SUPERUSER_PASSWORD}" \
    --email "${SUPERUSER_EMAIL}"
}

function run_tests()
{
  set -e
  echo "Running pep8 compliance check ..."
  flake8

  echo "Running unit tests ..."
  rm -rf cfy_wrapper/migrations
  python manage.py makemigrations cfy_wrapper
  python manage.py test $1
  set +e
}

case $1 in
  reset)
    reset "$2" "$3" "$4"
    ;;

  test)
    run_tests "$2"
    ;;

  *)
    run
    ;;
esac
