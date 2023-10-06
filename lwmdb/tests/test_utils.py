from collections.abc import Generator
from logging import INFO
from pathlib import Path

import pytest
from pandas import DataFrame, read_csv
from django.core.exceptions import FieldError

import census
from mitchells.import_fixtures import MITCHELLS_CSV_URL, MITCHELLS_EXCEL_URL
from newspapers.models import Newspaper, Issue

from ..utils import (
    VALID_FALSE_STRS,
    VALID_TRUE_STRS,
    DataSource,
    download_file,
    path_or_str_suffix,
    str_to_bool,
    # similar_records_pks,
)

# >>> call_command("loaddata",
# ...              "lwmdb/tests/initial_test_dataprovider.json")
# >>> for dp in DataProvider.objects.all():
# ...     print(dp)


@pytest.mark.parametrize("val", VALID_TRUE_STRS)
def test_str_to_bool_true(val) -> None:
    assert str_to_bool(val) == True
    assert str_to_bool(val.upper()) == True


@pytest.mark.parametrize("val", VALID_FALSE_STRS)
def test_str_to_bool_false(val) -> None:
    assert str_to_bool(val) == False
    assert str_to_bool(val.upper()) == False


def test_str_to_bool_true_invalid() -> None:
    with pytest.raises(ValueError):
        str_to_bool("Truue")


def test_path_or_str_suffix_path_csv() -> None:
    """Test extracting `.csv` extension from Path instance."""
    assert path_or_str_suffix(Path("cat") / "dog" / "fish.csv") == "csv"


@pytest.mark.download
@pytest.mark.slow
def test_download_large_csv(caplog, tmp_path) -> None:
    caplog.set_level(INFO)
    test_csv_path: Path = tmp_path / "test_file.csv"
    success: bool = download_file(test_csv_path, MITCHELLS_CSV_URL)
    assert success

    CORRECT_LOG_0: str = (
        f"{test_csv_path} not found, downloading from {MITCHELLS_CSV_URL}"
    )
    CORRECT_LOG_1: str = f"Saved to {test_csv_path}"
    CORRECT_LOG_2: str = f"{MITCHELLS_CSV_URL} file available from {test_csv_path}"
    assert caplog.messages == [CORRECT_LOG_0, CORRECT_LOG_1, CORRECT_LOG_2]


@pytest.mark.download
@pytest.mark.slow
def test_download_xlsx(caplog, tmp_path) -> None:
    """Test new download of `MITCHELLS_EXCEL_URL` to `tmp_path`."""
    caplog.set_level(INFO)
    test_xlsx_path: Path = tmp_path / "test.xlsx"
    success: bool = download_file(test_xlsx_path, MITCHELLS_EXCEL_URL)
    assert success
    LOG_0 = f"{test_xlsx_path} not found, downloading from {MITCHELLS_EXCEL_URL}"
    LOG_1 = f"Saved to {test_xlsx_path}"
    LOG_2 = f"{MITCHELLS_EXCEL_URL} file available from {test_xlsx_path}"
    assert caplog.messages == [LOG_0, LOG_1, LOG_2]


def test_download_local_path_folder_error(caplog, tmp_path) -> None:
    """Test downloading `MITCHELLS_EXCEL_URL` fixture."""
    caplog.set_level(INFO)
    success: bool = download_file(tmp_path, MITCHELLS_EXCEL_URL)
    assert not success
    LOG = f"{tmp_path} is not a file"
    assert caplog.messages == [LOG]


def test_download_invalid_url(caplog, tmp_path) -> None:
    """Test downloading invalid URL."""
    caplog.set_level(INFO)
    url: str = "not/a/url"
    success: bool = download_file(tmp_path, url)
    assert not success
    LOG = f"{url} is not a valid url"
    assert caplog.messages == [LOG]


@pytest.mark.xfail(reason="need to automate conditional http block")
def test_download_no_internet(caplog, tmp_path) -> None:
    """Test downloading with no internet connection."""
    caplog.set_level(INFO)
    test_xlsx_path: Path = tmp_path / "test.xlsx"
    success: bool = download_file(test_xlsx_path, MITCHELLS_EXCEL_URL)
    assert not success
    LOG_0 = f"{test_xlsx_path} not found, downloading from {MITCHELLS_EXCEL_URL}"
    LOG_1 = f"Download error (likely no internet connection): {MITCHELLS_EXCEL_URL}"
    assert caplog.messages == [LOG_0, LOG_1]


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


class TestDataSource:
    """Test creating and manipulating a remote csv DataSource."""

    def test_str(self, rsd_1851) -> None:
        """Test `str` `DataSource`."""
        assert str(rsd_1851) == "'demographics_en...csv' for `census` app data"

    def test_repr(self, rsd_1851) -> None:
        """Test `repr` of a `DataSource`."""
        assert repr(rsd_1851) == "DataSource('census', 'demographics_en...csv')"

    @pytest.mark.download
    def test_download(self, rsd_1851) -> None:
        """Test downloading without."""
        file: DataFrame = rsd_1851.read()
        assert rsd_1851.is_local
        assert len(file.columns) == 69


# class TestDBDupes:
# 
#     """Test checking and collection duplicate database records."""
# 
#     @pytest.mark.django_db
#     def test_inconsistent_models(self, newspaper_dupes_qs) -> None:
#         """Check raising error if `model` and `qs` are passed."""
#         correct_error_str: str = "`qs` model: <class 'newspapers.models.Issue'> != passed `model` <class 'newspapers.models.Newspaper'>"
#         with pytest.raises(ValueError) as exec_info:
#              similar_record_pks(Newspaper, Issue.objects.all())
#         assert str(exec_info.value) == correct_error_str
# 
#     @pytest.mark.django_db
#     def test_incorrect_fields(self, newspaper_dupes_qs) -> None:
#         """Check raising error if `model` and `qs` are passed."""
#         correct_error: ValueError = ValueError("`qs` model: <class 'newspapers.models.Issue'> != passed `model` <class 'newspapers.models.Newspaper'>")
#         with pytest.raises(FieldError) as exec_info:
#              similar_record_pks(Newspaper, dupe_fields=('id', 'elephant'))
#         assert "Cannot resolve keyword 'elephant'" in str(exec_info.value)

