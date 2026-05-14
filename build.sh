#!/usr/bin/env bash
# ref: Render Django deployment guide — https://render.com/docs/deploy-django
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py seed_demo_data