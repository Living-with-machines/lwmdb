from collections.abc import Generator
from os import chdir
from pathlib import Path
from pprint import pprint
from shutil import copyfile
from typing import Final

import pytest
from coverage_badge.__main__ import main as gen_cov_badge
from django.core.management import call_command
from django.db.models.query import QuerySet

# from django.conf import settings
from django.utils.translation import activate
from pandas import read_csv

import census
from lwmdb.utils import (
    DEFAULT_LOCAL_ENV_PATH,
    DataSource,
    DupeRecords,
    ProductionENVGenConfig,
    app_data_path,
)
from mitchells.import_fixtures import MITCHELLS_EXCEL_PATH
from newspapers.models import DataProvider, FullText, Issue, Item, Newspaper
from newspapers.utils import path_to_newspaper_code

ROOT_PATH: Path = Path().absolute()
LWMDB_TEST_FIXTURES_PATH: Final[Path] = Path("./lwmdb/tests").absolute()
BADGE_PATH: Final[Path] = Path("docs") / "assets" / "coverage.svg"
PLAINTEXT_PATH_COMPRESSED: Final[Path] = Path("0003548_plaintext.zip")
PLAINTEXT_PATH: Final[Path] = Path("0003548/1904/0707/0003548_19040707_art0037.txt")

DATA_PROVIDER_INITIAL_FIXTURE_PATH: Final[Path] = (
    LWMDB_TEST_FIXTURES_PATH / "initial-test-dataprovider.json"
)
DATA_PROVIDER_CORRECTED_FIXTURE_PATH: Final[Path] = (
    LWMDB_TEST_FIXTURES_PATH / "update-test-dataprovider.json"
)
MITCHELLS_APP_EXCEL_PATH: Final[Path] = (
    app_data_path("mitchells") / MITCHELLS_EXCEL_PATH
)


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


@pytest.fixture
def root_dir() -> Path:
    """Return `lwmdb` installation `Path`."""
    return ROOT_PATH


@pytest.fixture
def local_env_copy_path(tmp_path: Path) -> Path:
    """Create a test copy of `DEFAULT_LOCAL_ENV_PATH`."""
    test_local_config_path: Path = tmp_path / Path(DEFAULT_LOCAL_ENV_PATH)
    test_local_config_path.parent.mkdir(parents=True, exist_ok=True)
    return copyfile(DEFAULT_LOCAL_ENV_PATH, test_local_config_path)


@pytest.fixture
def production_config_manager(local_env_copy_path: Path) -> ProductionENVGenConfig:
    """Test example `ProductionENVGenConfig` configuration."""
    chdir(local_env_copy_path.parents[1])
    return ProductionENVGenConfig()


@pytest.fixture(autouse=True)
def media_storage(settings, tmp_path: Path) -> None:
    """Generate a temp path for testing media files."""
    settings.MEDIA_ROOT = str(tmp_path)


@pytest.mark.slow
@pytest.mark.download
@pytest.fixture(scope="session")
def mitchells_data_path(tmp_path_factory) -> Generator[Path, None, None]:
    """Return path to `mitchells` app data."""
    tmp_path: Path = tmp_path_factory.mktemp("mitchells_data")
    yield tmp_path / MITCHELLS_APP_EXCEL_PATH.name


@pytest.fixture
def old_data_provider_fixture_path(tmp_path: Path) -> Path:
    """Load initial example `newspaper.DataProvider` fixture."""
    return copyfile(
        DATA_PROVIDER_INITIAL_FIXTURE_PATH,
        tmp_path / DATA_PROVIDER_INITIAL_FIXTURE_PATH.name,
    )


@pytest.fixture
def updated_data_provider_fixture_path(tmp_path: Path) -> Path:
    """Load updated example `newspaper.DataProvider` fixture."""
    return copyfile(
        DATA_PROVIDER_CORRECTED_FIXTURE_PATH,
        tmp_path / DATA_PROVIDER_CORRECTED_FIXTURE_PATH.name,
    )


@pytest.fixture
@pytest.mark.django_db
def old_data_provider(old_data_provider_fixture_path: Path) -> None:
    """Load old example `newspaper.DataProvider` fixture."""
    call_command("loaddata", old_data_provider_fixture_path)


@pytest.fixture
@pytest.mark.django_db
def current_data_providers(updated_data_provider_fixture_path: Path) -> None:
    """Load old example `newspaper.DataProvider` fixture."""
    call_command("loaddata", updated_data_provider_fixture_path)


@pytest.fixture
@pytest.mark.django_db
def lwm_data_provider(current_data_providers) -> DataProvider:
    """Return the `bl-lwm` `DataProvider` instance."""
    return DataProvider.objects.get(code="bl-lwm")


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
def new_tredegar_last_issue_first_item_fulltext() -> FullText:
    """`FullText` fixture to use with `new_tredegar_last_issue_first_item`."""
    fulltext = FullText(
        text="An excellent full article",
        text_compressed_path=str(PLAINTEXT_PATH_COMPRESSED),
        text_path=str(PLAINTEXT_PATH),
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
def newspaper_dupe_config(newspaper_dupes_qs: QuerySet) -> DupeRecords:
    """Create example `DupeRecords` from `newspaper_dupes_qs`."""
    return DupeRecords(
        newspaper_dupes_qs,
        dupe_method_kwargs={"null_relations": ("issue",)},
    )


@pytest.fixture
def rsd_1851() -> Generator[DataSource, None, None]:
    """Example csv DataSource."""
    rsd: DataSource = DataSource(
        file_name="demographics_england_wales_1851.csv",
        app=census,
        url="https://reshare.ukdataservice.ac.uk/853547/4/1851_RSD_data.csv",
        read_func=read_csv,
        description="Demographic and socio-economic variables for Registration Sub-Districts (RSDs) in England and Wales, 1851",
        citation="https://dx.doi.org/10.5255/UKDA-SN-853547",
        license="http://creativecommons.org/licenses/by/4.0/",
    )
    yield rsd
    rsd.delete()


@pytest.fixture(autouse=True)
def doctest_auto_fixtures(doctest_namespace: dict) -> None:
    """Elements to add to default `doctest` namespace."""
    doctest_namespace["pprint"] = pprint


def pytest_sessionfinish(session, exitstatus):
    """Generate badges for docs after tests finish."""
    if exitstatus == 0:
        BADGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        gen_cov_badge(["-o", f"{BADGE_PATH}", "-f"])
