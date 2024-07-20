#!/bin/sh

# Apply database migrations
python manage.py makemigrations
python manage.py migrate

# Stop any running Celery workers and beat
pkill -f 'celery worker'
pkill -f 'celery beat'

# Purge Celery tasks
celery -A vunderkids purge -f

# Remove the celerybeat-schedule file
rm -f /code/celerybeat-schedule

# Start Gunicorn and Celery services
gunicorn vunderkids.wsgi --bind 0.0.0.0:8000 &
celery -A vunderkids worker --loglevel=info &
celery -A vunderkids beat --loglevel=info --schedule=/code/celerybeat-schedule
