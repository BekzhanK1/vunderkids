# settings/production.py

from .base import *
import dj_database_url

DEBUG = False

ALLOWED_HOSTS = [
    'https://vunderkids.kz', 'https://www.vunderkids.kz',
    'http://85.198.90.24', 'http://localhost', 'http://127.0.0.1',
    'vunderkids.kz', 'www.vunderkids.kz', 'api.vunderkids.kz'
]

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://vunderkids.kz",
    "https://www.vunderkids.kz",
]

CSRF_TRUSTED_ORIGINS = [
    'https://www.vunderkids.kz',
    'https://vunderkids.kz',
    'https://api.vunderkids.kz'
]

FRONTEND_URL = "https://vunderkids.kz/"

DATABASES = {
    'default': dj_database_url.config(
        default='postgres://postgres:1234@localhost:5432/vunderkids'
    )
}

CELERY_BROKER_URL = 'amqp://guest:guest@rabbitmq:5672//'
CELERY_RESULT_BACKEND = 'rpc://'



