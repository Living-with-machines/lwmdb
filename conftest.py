from pathlib import Path
from pprint import pprint

import pytest
from coverage_badge.__main__ import main as gen_cov_badge
from django.core.management import call_command
from django.db.models.query import QuerySet

# from django.conf import settings
from django.utils.translation import activate

from fulltext.models import Fulltext
from lwmdb.utils import DupeRemoveConfig, app_data_path
from mitchells.import_fixtures import MITCHELLS_EXCEL_PATH
from newspapers.models import DataProvider, Issue, Item, Newspaper
from newspapers.utils import path_to_newspaper_code

BADGE_PATH: Path = Path("docs") / "assets" / "coverage.svg"
PLAINTEXT_PATH_COMPRESSED: Path = Path("0003548_plaintext.zip")
PLAINTEXT_PATH: Path = Path("0003548/1904/0707/0003548_19040707_art0037.txt")


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
    """Return the `bl_lwm` `DataProvider` instance."""
    return DataProvider.objects.get(code="bl_lwm")


@pytest.fixture
@pytest.mark.django_db
def new_tredegar_newspaper() -> Newspaper:
    """`Newspaper` using example `PLAINTEXT_PATH` fixture.

    Note:
        The `PLAINTEXT_PATH.parents` test fxiture includes the newspaper
        `publication_code`, then `year`, then `month_day`. This extracts
        that `publication_code` for efficiency.
    """
    new_tredegar = Newspaper(
        publication_code=path_to_newspaper_code(PLAINTEXT_PATH, "publication"),
        title=("New Tredegar, Bargoed & Caerphilly Journal"),
        location="Bedwellty, Gwent, Wales",
    )
    new_tredegar.save()
    return new_tredegar


@pytest.fixture
@pytest.mark.django_db
def new_tredegar_last_issue(new_tredegar_newspaper) -> Issue:
    """`Newspaper` `Issue` using example `PLAINTEXT_PATH` fixture.

    Note:
        The `PLAINTEXT_PATH.parents` test fxiture includes the newspaper
        `publication_code`, then `year`, then `month_day`. This extracts
        that `issue_code` for ease in maintaining tests.
    """
    last_issue = Issue(
        issue_code=path_to_newspaper_code(PLAINTEXT_PATH, "issue"),
        input_sub_path=str(PLAINTEXT_PATH.parent),
        newspaper=new_tredegar_newspaper,
        issue_date="1904-07-07",
    )
    last_issue.save()
    return last_issue


@pytest.fixture
@pytest.mark.django_db
def new_tredegar_last_issue_first_item(
    new_tredegar_last_issue,
    lwm_data_provider,
) -> Item:
    """`Item` from `new_tredegar_last_issue` and `lwm_data_provider`."""
    item = Item(
        item_code=path_to_newspaper_code(PLAINTEXT_PATH, "item"),
        title="MEETING AT CAERPHILLY.",
        item_type="ARTICLE",
        ocr_quality_mean=0.8526,
        ocr_quality_sd=0.2192,
        input_filename=PLAINTEXT_PATH.name,
        issue=new_tredegar_last_issue,
        word_count=1261,
        data_provider=lwm_data_provider,
    )
    item.save()
    return item


@pytest.fixture
@pytest.mark.django_db
def new_tredegar_last_issue_first_item_fulltext() -> Fulltext:
    """`Fulltext` fixture to use with `new_tredegar_last_issue_first_item`."""
    fulltext = Fulltext(
        text="An excellent full article",
        compressed_path=str(PLAINTEXT_PATH_COMPRESSED),
        path=str(PLAINTEXT_PATH),
    )
    fulltext.save()
    return fulltext


@pytest.fixture
@pytest.mark.django_db
def newspaper_dupes_qs(
    new_tredegar_newspaper: Newspaper, new_tredegar_last_issue: Issue
) -> QuerySet:
    """Create model fixtures with a dupe for testing."""
    Newspaper.objects.bulk_create(
        [
            Newspaper(
                publication_code=new_tredegar_newspaper.publication_code,
                title=new_tredegar_newspaper.title,
                location=new_tredegar_newspaper.location,
            ),
            Newspaper(publication_code="0002648", title="Not Dupe News"),
        ]
    )
    return Newspaper.objects.all()


@pytest.fixture
@pytest.mark.django_db
def newspaper_dupe_rm_config(newspaper_dupes_qs: QuerySet) -> DupeRemoveConfig:
    """Create example `DupeRmoveConfig` from `newspaper_dupes_qs`."""
    return DupeRemoveConfig(
        newspaper_dupes_qs,
        dupe_method_kwargs={"null_relations": ("issue",)},
    )


@pytest.fixture(autouse=True)
def doctest_auto_fixtures(doctest_namespace: dict) -> None:
    """Elements to add to default `doctest` namespace."""
    doctest_namespace["pprint"] = pprint


def pytest_sessionfinish(session, exitstatus):
    """Generate badges for docs after tests finish."""
    if exitstatus == 0:
        BADGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        gen_cov_badge(["-o", f"{BADGE_PATH}", "-f"])
