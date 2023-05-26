import pytest

# from django.conf import settings
from django.core.management import call_command
from django.utils.translation import activate


@pytest.fixture(autouse=True)
def set_default_language():
    """Ensure `en-gb` localisation is enforced for testing."""
    activate("en-gb")


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Call the `loaddata` command to provide test fixtures."""
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
        )


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    """Generate a temp path for testing media files."""
    settings.MEDIA_ROOT = tmpdir.strpath
