from logging import INFO

import pytest

from mitchells.import_fixtures import MITCHELLS_LOCAL_LINK_CSV_URL

from ..utils import VALID_FALSE_STRS, VALID_TRUE_STRS, download_file, str_to_bool


@pytest.mark.parametrize("val", VALID_TRUE_STRS)
def test_str_to_bool_true(val):
    assert str_to_bool(val) == True
    assert str_to_bool(val.upper()) == True


@pytest.mark.parametrize("val", VALID_FALSE_STRS)
def test_str_to_bool_false(val):
    assert str_to_bool(val) == False
    assert str_to_bool(val.upper()) == False


def test_str_to_bool_true_invalid():
    with pytest.raises(ValueError):
        str_to_bool("Truue")


@pytest.mark.slow
@pytest.mark.remotedata
def test_download_file(caplog, tmp_path):
    caplog.set_level(INFO)
    test_csv_path = tmp_path / "test_file.csv"
    success = download_file(test_csv_path, MITCHELLS_LOCAL_LINK_CSV_URL)
    assert success

    CORRECT_DOWNLOAD_LOG_1 = (
        f"{test_csv_path} not found, downloading from {MITCHELLS_LOCAL_LINK_CSV_URL}"
    )
    CORRECT_DOWNLOAD_LOG_2 = f"Saved to {test_csv_path}"
    assert caplog.messages == [CORRECT_DOWNLOAD_LOG_1, CORRECT_DOWNLOAD_LOG_2]
