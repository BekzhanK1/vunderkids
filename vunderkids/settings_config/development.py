# settings/development.py

from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True
FRONTEND_URL = "http://localhost:5173/"
BACKEND_URL = "http://localhost:8000/"

DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")

DATABASE_TYPE = os.getenv("DATABASE_TYPE")
print(f"database = {DATABASE_TYPE}")
print(f"database = {DATABASE_NAME}")
print(f"database = {DATABASE_USER}")
print(f"database = {DATABASE_PASSWORD}")
print(f"database = {DATABASE_HOST}")
print(f"database = {DATABASE_PORT}")


if DATABASE_TYPE == "POSTGRES":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": DATABASE_NAME,
            "USER": DATABASE_USER,
            "PASSWORD": DATABASE_PASSWORD,
            "HOST": DATABASE_HOST,
            "PORT": DATABASE_PORT,
        }
    }
    print("POSTGRES IS RUNNING")
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }
    print("SQLITE IS RUNNING")

CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/0"
