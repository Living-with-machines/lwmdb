from django.utils.translation import activate
# from django.conf import settings
from django.core.management import call_command
import pytest


@pytest.fixture(autouse=True)
def set_default_language():
    activate('en-gb')


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("loaddata",)
