"""
With these settings, tests run faster.
"""

from .settings import *  # noqa
from .settings import config

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# SECRET_KEY = config(
#     "DJANGO_SECRET_KEY",
#     default="4R2Fx8e5Z1kOMztBE62kEJvwENiNrGmN83I38B7XZvbOABHCUMWwe4Byt7a6n64i",
# )
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# DEBUGING FOR TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[0]["OPTIONS"]["debug"] = True  # type: ignore # noqa F405

# Your stuff...
# ------------------------------------------------------------------------------
# DATABASES = {
#     "default": {
#         'ENGINE': 'django.contrib.gis.db.backends.postgis',
#         'NAME': config['POSTGRES_DB'],  # Perhaps a different name...?
#         'USER': config['POSTGRES_USER'],
#         'PASSWORD': config['POSTGRES_PASSWORD'],
#         'HOST': config['POSTGRES_HOST'],
#     },
#     # "local": {
#     #     "ENGINE": "django.db.backends.sqlite3",
#     #     "NAME": BASE_DIR / "db.sqlite3",
#     # },
# }
