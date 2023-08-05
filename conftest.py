from pathlib import Path

import pytest
from coverage_badge.__main__ import main as gen_cov_badge

# from django.conf import settings
from django.utils.translation import activate

from lwmdb.utils import app_data_path
from mitchells.import_fixtures import MITCHELLS_EXCEL_PATH

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
