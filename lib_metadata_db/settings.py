import os

from dotenv import load_dotenv

load_dotenv()

DEBUG = True
ALLOWED_HOSTS = ["*"]

SECRET_KEY = os.getenv("SECRET_KEY")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME_NEWSPAPERS"),
        "USER": os.getenv("DB_USERNAME_NEWSPAPERS"),
        "PASSWORD": os.getenv("DB_PASSWORD_NEWSPAPERS"),
        "HOST": os.getenv("DB_HOST_NEWSPAPERS"),
        "PORT": os.getenv("PORT"),
        "ATOMIC_REQUESTS": True,
    },
    "newspapers_db": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME_NEWSPAPERS"),
        "USER": os.getenv("DB_USERNAME_NEWSPAPERS"),
        "PASSWORD": os.getenv("DB_PASSWORD_NEWSPAPERS"),
        "HOST": os.getenv("DB_HOST_NEWSPAPERS"),
        "PORT": os.getenv("PORT"),
        "ATOMIC_REQUESTS": True,
    },
}


INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "newspapers.apps.NewspapersConfig",
]

USE_TZ = False
TIME_ZONE = "GB"
