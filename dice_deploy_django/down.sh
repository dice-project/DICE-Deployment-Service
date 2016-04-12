#!/bin/bash

kill -3 $(cat gunicorn.pid)
celery multi stop main-worker@localhost
