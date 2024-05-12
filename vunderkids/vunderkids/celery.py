from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vunderkids.settings')

app = Celery('vunderkids')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


# celery.py or where you configure Celery

app.conf.beat_schedule = {
    'send_daily_email_to_all_students': {
        'task': 'account.tasks.send_daily_email_to_all_students',
        'schedule': crontab(hour=21, minute=50),  # Executes every day at 8:00 AM
    },
    'send_daily_email_to_all_parents': {
        'task': 'account.tasks.send_daily_email_to_all_parents',
        'schedule': crontab(hour=21, minute=51),  # Executes every day at 8:00 AM
    },
}
