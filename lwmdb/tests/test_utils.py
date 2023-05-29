from logging import INFO
from pathlib import Path

import pytest

from mitchells.import_fixtures import (
    MITCHELLS_LOCAL_LINK_CSV_URL,
    MITCHELLS_LOCAL_LINK_EXCEL_URL,
)

from ..utils import VALID_FALSE_STRS, VALID_TRUE_STRS, download_file, str_to_bool


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


@pytest.mark.slow
def test_download_large_csv(caplog, tmp_path) -> None:
    caplog.set_level(INFO)
    test_csv_path: Path = tmp_path / "test_file.csv"
    success: bool = download_file(test_csv_path, MITCHELLS_LOCAL_LINK_CSV_URL)
    assert success

    CORRECT_LOG_0: str = (
        f"{test_csv_path} not found, downloading from {MITCHELLS_LOCAL_LINK_CSV_URL}"
    )
    CORRECT_LOG_1: str = f"Saved to {test_csv_path}"
    CORRECT_LOG_2: str = (
        f"{MITCHELLS_LOCAL_LINK_CSV_URL} file available from {test_csv_path}"
    )
    assert caplog.messages == [CORRECT_LOG_0, CORRECT_LOG_1, CORRECT_LOG_2]


@pytest.mark.slow
def test_download_xlsx(caplog, tmp_path) -> None:
    """Test new download of `MITCHELLS_LOCAL_LINK_EXCEL_URL` to `tmp_path`."""
    caplog.set_level(INFO)
    test_xlsx_path: Path = tmp_path / "test.xlsx"
    success: bool = download_file(test_xlsx_path, MITCHELLS_LOCAL_LINK_EXCEL_URL)
    assert success
    LOG_0 = (
        f"{test_xlsx_path} not found, downloading from {MITCHELLS_LOCAL_LINK_EXCEL_URL}"
    )
    LOG_1 = f"Saved to {test_xlsx_path}"
    LOG_2 = f"{MITCHELLS_LOCAL_LINK_EXCEL_URL} file available from {test_xlsx_path}"
    assert caplog.messages == [LOG_0, LOG_1, LOG_2]


def test_download_local_path_folder_error(caplog, tmp_path) -> None:
    """Test downloading `MITCHELLS_LOCAL_LINK_EXCEL_URL` fixture."""
    caplog.set_level(INFO)
    success: bool = download_file(tmp_path, MITCHELLS_LOCAL_LINK_EXCEL_URL)
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
    success: bool = download_file(test_xlsx_path, MITCHELLS_LOCAL_LINK_EXCEL_URL)
    assert not success
    LOG_0 = (
        f"{test_xlsx_path} not found, downloading from {MITCHELLS_LOCAL_LINK_EXCEL_URL}"
    )
    LOG_1 = f"Download error (likely no internet connection): {MITCHELLS_LOCAL_LINK_EXCEL_URL}"
    assert caplog.messages == [LOG_0, LOG_1]
