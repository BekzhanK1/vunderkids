# vunderkids
## Celery worker
celery -A vunderkids worker -l info

## Beat
celery -A vunderkids beat --loglevel=info
