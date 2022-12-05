from django.utils.translation import activate
import pytest


@pytest.fixture(autouse=True)
def set_default_language():
    activate('en-gb')
