"""ASGI config for lwmdb project.

It exposes the ASGI callable as a module-level variable named
`application`.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from dotenv import load_dotenv

from lwmdb.utils import str_to_bool

load_dotenv()

PRODUCTION: bool = str_to_bool(os.getenv("PRODUCTION", "False"))

if PRODUCTION:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.production")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
