from typing import Any, Final

from .settings import *  # noqa

DEFAULT_ALLOWED_HOSTS: Final[list[str]] = ["lwmdb.livingwithmachines.ac.uk", "0.0.0.0"]
DEFAULT_CONN_MAX_AGE: Final[int] = 60
DEFAULT_SECURE_SSL_REDIRECT: Final[bool] = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
DEFAULT_SECURE_HSTS_INCLUDE_SUBDOMAINS: Final[bool] = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
DEFAULT_SECURE_HSTS_PRELOAD: Final[bool] = True
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
DEFAULT_SECURE_CONTENT_TYPE_NOSNIFF: Final[bool] = True
DEFAULT_FROM_EMAIL: Final[str] = "lwmdb <noreply@lwmdb.livingwithmachines.ac.uk>"
# https://docs.djangoproject.com/en/dev/ref/settings/#server-email
DEFAULT_SERVER_EMAIL: Final[str] = DEFAULT_FROM_EMAIL
# https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
DEFAULT_EMAIL_SUBJECT_PREFIX: Final[str] = "[lwmdb]"

default_config: Final[dict[str, Any]] = {
    "DJANGO_ALLOWED_HOSTS": DEFAULT_ALLOWED_HOSTS,
    "DJANGO_CONN_MAX_AGE": DEFAULT_ALLOWED_HOSTS,
    "DJANGO_SECURE_SSL_REDIRECT": DEFAULT_SECURE_SSL_REDIRECT,
    "DJANGO_SECURE_SSL_REDIRECT": DEFAULT_SECURE_SSL_REDIRECT,
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS": DEFAULT_SECURE_HSTS_INCLUDE_SUBDOMAINS,
    "DJANGO_SECURE_HSTS_PRELOAD": DEFAULT_SECURE_HSTS_PRELOAD,
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF": DEFAULT_SECURE_CONTENT_TYPE_NOSNIFF,
    "DJANGO_DEFAULT_FROM_EMAIL": DEFAULT_FROM_EMAIL,
    "DJANGO_SERVER_EMAIL": DEFAULT_SERVER_EMAIL,
    "DJANGO_EMAIL_SUBJECT_PREFIX": DEFAULT_EMAIL_SUBJECT_PREFIX,
}

config = {**default_config, **config}  # noqa F405

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL regex.
# ADMIN_URL = config["DJANGO_ADMIN_URL"]
# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# SECRET_KEY = config["DJANGO_SECRET_KEY"]
SECRET_KEY = config["SECRET_KEY"]
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
# ALLOWED_HOSTS = config["DJANGO_ALLOWED_HOSTS"]
ALLOWED_HOSTS = config["DJANGO_ALLOWED_HOSTS"]
# ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["lwmdb.livingwithmachines.ac.uk"])

# DATABASES
# ------------------------------------------------------------------------------
# DEFAULT_CONN_MAX_AGE: Final[int] =  60

# DATABASES["default"] = config["POSTGRES_HOST"]  # noqa F405
# DATABASES["default"]["ATOMIC_REQUESTS"] = True  # noqa F405
# DATABASES["default"]["CONN_MAX_AGE"] = config["DJANGO_CONN_MAX_AGE"]  # noqa F405

# CACHES
# ------------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config["REDIS_URL"],
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Mimicing memcache behavior.
            # https://github.com/jazzband/django-redis#memcached-exceptions-behavior
            "IGNORE_EXCEPTIONS": True,
        },
    }
}

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = config["DJANGO_SECURE_SSL_REDIRECT"]
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
# TODO: set this to 60 seconds first and then to 518400 once you prove the former works
SECURE_HSTS_SECONDS = 60
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
# SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
#     "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True
# )
SECURE_HSTS_INCLUDE_SUBDOMAINS = config["DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS"]
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
SECURE_HSTS_PRELOAD = config["DJANGO_SECURE_HSTS_PRELOAD"]
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = config["DJANGO_SECURE_CONTENT_TYPE_NOSNIFF"]

# STATIC
# ------------------------
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# MEDIA
# ------------------------------------------------------------------------------

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
DEFAULT_FROM_EMAIL = config["DJANGO_DEFAULT_FROM_EMAIL"]
# https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = config["DJANGO_SERVER_EMAIL"]
# https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = config["DJANGO_EMAIL_SUBJECT_PREFIX"]

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL regex.
# ADMIN_URL = config["DJANGO_ADMIN_URL"]

# Anymail
# ------------------------------------------------------------------------------
# https://anymail.readthedocs.io/en/stable/installation/#installing-anymail
INSTALLED_APPS += ["anymail"]  # noqa F405
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
# https://anymail.readthedocs.io/en/stable/installation/#anymail-settings-reference
# https://anymail.readthedocs.io/en/stable/esps
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
ANYMAIL = {}


# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["console", "mail_admins"],
            "propagate": True,
        },
    },
}

# Your stuff...
# ------------------------------------------------------------------------------
