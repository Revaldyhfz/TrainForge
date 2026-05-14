#!/usr/bin/env bash
# build script for Render deployment
# ref: Render Django deployment guide — https://render.com/docs/deploy-django
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
