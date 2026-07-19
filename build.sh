#!/usr/bin/env bash
# Render build script: install dependencies, collect static files, apply migrations
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
