from pathlib import Path

import pytest
from coverage_badge.__main__ import main as gen_cov_badge
from django.core.management import call_command

# from django.conf import settings
from django.utils.translation import activate

from lwmdb.utils import app_data_path
from mitchells.import_fixtures import MITCHELLS_EXCEL_PATH
from newspapers.models import DataProvider

BADGE_PATH: Path = Path("docs") / "assets" / "coverage.svg"


@pytest.fixture(autouse=True)
def set_default_language() -> None:
    """Ensure `en-gb` localisation is enforced for testing."""
    activate("en-gb")


# @pytest.fixture(scope="session")
# def django_db_setup(django_db_setup, django_db_blocker):
#     """Call the `loaddata` command per app to provide test fixtures."""
#     with django_db_blocker.unblock():
#         call_command(
#             "loaddata",
#         )


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir) -> None:
    """Generate a temp path for testing media files."""
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture(scope="session")
def mitchells_data_path() -> Path:
    """Return path to `mitchells` app data."""
    return app_data_path("mitchells") / MITCHELLS_EXCEL_PATH


def pytest_sessionfinish(session, exitstatus):
    """Generate badges for docs after tests finish."""
    if exitstatus == 0:
        BADGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        gen_cov_badge(["-o", f"{BADGE_PATH}", "-f"])


@pytest.fixture
def old_data_provider_fixture_path() -> Path:
    """Load old example `newspaper.DataProvider` fixture."""
    return Path("lwmdb/tests/initial-test-dataprovider.json")


@pytest.fixture
def updated_data_provider_path() -> Path:
    """Load old example `newspaper.DataProvider` fixture."""
    return Path("lwmdb/tests/update-test-dataprovider.json")


@pytest.fixture
@pytest.mark.django_db
def old_data_provider(old_data_provider_fixture_path: Path) -> None:
    """Load old example `newspaper.DataProvider` fixture."""
    call_command("loaddata", old_data_provider_fixture_path)


@pytest.fixture
@pytest.mark.django_db
def current_data_providers(updated_data_provider_path: Path) -> None:
    """Load old example `newspaper.DataProvider` fixture."""
    call_command("loaddata", updated_data_provider_path)


@pytest.fixture
@pytest.mark.django_db
def lwm_data_provider(current_data_providers) -> DataProvider:
    """Return the `lwm-bl` `DataPRovider` instance."""
    return DataProvider.objects.get(code="bl_lwm")
