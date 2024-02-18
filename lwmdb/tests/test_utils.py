from logging import INFO
from pathlib import Path
from typing import Any

import pytest
from django.core.exceptions import FieldError
from django.db.models import QuerySet
from pandas import DataFrame

from mitchells.import_fixtures import MITCHELLS_CSV_URL, MITCHELLS_EXCEL_URL
from newspapers.models import Issue, Newspaper

from ..utils import (
    VALID_FALSE_STRS,
    VALID_TRUE_STRS,
    DupeRecords,
    download_file,
    dupes_to_check,
    filter_by_null_fk,
    path_or_str_suffix,
    qs_difference,
    similar_records,
    str_to_bool,
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
    """Test downloading with no internet connection.

    Note:
        * While British Library data downloading is blocked, this passes.
    """
    caplog.set_level(INFO)
    test_xlsx_path: Path = tmp_path / "test.xlsx"
    success: bool = download_file(test_xlsx_path, MITCHELLS_EXCEL_URL)
    assert not success
    LOG_0 = f"{test_xlsx_path} not found, downloading from {MITCHELLS_EXCEL_URL}"
    LOG_1 = f"Download error (likely no internet connection): {MITCHELLS_EXCEL_URL}"
    assert caplog.messages == [LOG_0, LOG_1]


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


class TestDBDupes:
    """Test checking and collection duplicate database records."""

    @pytest.mark.django_db
    def test_incorrect_fields(self, newspaper_dupes_qs: QuerySet) -> None:
        """Check raising error if `check_fields` are not in `qs.model`."""
        with pytest.raises(FieldError) as exec_info:
            similar_records(Newspaper, check_fields=("id", "elephant"))
        assert "Cannot resolve keyword 'elephant'" in str(exec_info.value)

    @pytest.mark.parametrize(
        "to_delete_count, to_keep_count, dupe_fields, dupe_method_kwargs",
        (
            (1, 1, ("publication_code",), {"null_relations": ("issue",)}),
            (2, 1, ("publication_code",), {"null_relations": ("issue",)}),
            (10, 1, ("publication_code",), {"null_relations": ("issue",)}),
        ),
    )
    @pytest.mark.django_db
    def test_dupes_to_check(
        self,
        newspaper_dupes_qs: QuerySet,
        to_delete_count: int,
        to_keep_count: int,
        dupe_fields: tuple[str, ...],
        dupe_method_kwargs: dict[str, Any],
    ) -> None:
        """Check raising error if `check_fields` are not in `qs.model`."""
        for _ in range(to_delete_count - 1):
            new_dupe: Newspaper = newspaper_dupes_qs[1]
            new_dupe.pk = None
            new_dupe.save()

        dupes_rm_config: DupeRecords = dupes_to_check(
            Newspaper, dupe_fields=dupe_fields, dupe_method_kwargs=dupe_method_kwargs
        )

        assert len(dupes_rm_config) == to_delete_count + to_keep_count
        assert len(dupes_rm_config.records_to_delete) == to_delete_count
        assert len(dupes_rm_config.records_to_keep) == to_keep_count
        assert set(
            dupes_rm_config.all_dupe_records.intersection(
                dupes_rm_config.records_to_delete
            )
        ) == set(dupes_rm_config.records_to_delete)
        assert set(
            dupes_rm_config.all_dupe_records.intersection(
                dupes_rm_config.records_to_keep
            )
        ) == set(dupes_rm_config.records_to_keep)

    @pytest.mark.parametrize(
        "new_dupes, to_delete_count, to_keep_count, include_issue",
        ((0, 3, 0, False), (1, 4, 0, False), (2, 5, 0, False), (10, 8, 5, True)),
    )
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_filter_by_null_relations(
        self,
        newspaper_dupes_qs: QuerySet,
        new_dupes: int,
        to_delete_count: int,
        to_keep_count: int,
        include_issue: bool,
    ) -> None:
        """Check raising error if `check_fields` are not in `qs.model`.

        Todo:
            * Recheck less complex examples
            * Add examples where `is_null = False`
        """
        no_included_fks: QuerySet
        at_least_one_included_fk: QuerySet

        for i in range(new_dupes):
            new_dupe: Newspaper = newspaper_dupes_qs[1]
            new_dupe.pk = None
            new_dupe.save()
            if i > 2 and i % 2:
                new_issue: Issue = Issue(issue_date="1865-06-19")
                new_issue.newspaper_id = new_dupe.id
                new_issue.issue_code = f"{new_dupe.publication_code}-18650619"
                new_issue.input_sub_path = "0003040/1865/0619"
                new_issue.save()
        null_relations: tuple[str, ...] = ("issue",) if include_issue else ()
        no_included_fks = filter_by_null_fk(
            Newspaper.objects.all(), null_relations=null_relations
        )
        at_least_one_included_fk = qs_difference(
            Newspaper.objects.all(),
            no_included_fks,
        )
        assert len(no_included_fks) == to_delete_count
        assert len(at_least_one_included_fk) == to_keep_count
