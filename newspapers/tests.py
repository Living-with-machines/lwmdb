from datetime import datetime
from logging import DEBUG
from pathlib import Path
from typing import Final

import pytest
from django.conf import settings

from lwmdb.utils import truncate_str, word_count

from .models import (
    CODE_SEPERATOR_CHAR,
    MAX_PRINT_SELF_STR_LENGTH,
    DataProvider,
    FullText,
    Issue,
    Item,
    Newspaper,
)

TEST_NEWSPAPER_CODE: Final[str] = "0003040"
TEST_ISSUE_CODE: Final[str] = CODE_SEPERATOR_CHAR.join(
    [TEST_NEWSPAPER_CODE, "18940905"]
)
TEST_ITEM_CODE_PREFIX: Final[str] = CODE_SEPERATOR_CHAR.join(
    [TEST_ISSUE_CODE, "art0030"]
)
TEST_ITEM_CODE: Final[str] = TEST_ITEM_CODE_PREFIX + "502"
TEST_ITEM_INPUT_FILENAME: Final[str] = "0003040_18940905_art0030502.txt"
TEST_ITEM_TITLE: Final[str] = "SAD END OF A RAILWAY"
TEST_ITEM_TITLE_CHAR_COUNT: Final[int] = 20
TEST_ITEM_TITLE_WORD_COUNT: Final[int] = 5

MODULE_LOG_PREFIX: Final[str] = "DEBUG    newspapers.models:models.py:"


@pytest.mark.django_db
@pytest.fixture
def birkhead_newspaper() -> Newspaper:
    """Test Birkenhead `Newspaper` fixture."""
    return Newspaper.objects.create(
        publication_code=TEST_NEWSPAPER_CODE,
        title="The Birkenhead News and Wirral General Advertiser",
    )


@pytest.mark.django_db
@pytest.fixture
def issue_1894_sep_5(birkhead_newspaper: Newspaper) -> Issue:
    """Test 1894 September 5th Birkenhead Newspaper `Issue` fixture."""
    return Issue.objects.create(
        issue_code=TEST_ISSUE_CODE,
        issue_date=datetime(year=1894, month=9, day=5),
        input_sub_path="0003040/1894/0905",
        newspaper=birkhead_newspaper,
    )


@pytest.mark.django_db
@pytest.fixture
def bl_lwm_data_provider() -> DataProvider:
    """Test `bl_lwm` `DataProvider` fixture."""
    return DataProvider.objects.create(
        name="bl_lwm", collection="newspapers", source_note=""
    )


@pytest.mark.django_db
@pytest.fixture
def item_1894_sep_5(
    issue_1894_sep_5: Issue, bl_lwm_data_provider: DataProvider
) -> Item:
    """Test 5 September 1984 Birkenhead `Item` (story) fixture."""
    return Item.objects.create(
        item_code=TEST_ITEM_CODE,
        title=TEST_ITEM_TITLE,
        input_filename=TEST_ITEM_INPUT_FILENAME,
        issue=issue_1894_sep_5,
        data_provider=bl_lwm_data_provider,
    )


@pytest.mark.django_db
class TestItems:
    """Test creating and querying Item, Issue and Newpaper instances."""

    def test_item_parameters(self, item_1894_sep_5: Item) -> None:
        item = Item.objects.get(item_code=TEST_ITEM_CODE)
        assert item == item_1894_sep_5

        assert item.title == TEST_ITEM_TITLE
        assert item.data_provider.name == "bl_lwm"
        assert item.zip_file == "0003040_plaintext.zip"
        assert item.text_path == Path("0003040/1894/0905/") / TEST_ITEM_INPUT_FILENAME
        assert item.text_container == "bl_lwm-alto2txt"

        assert item.download_dir == Path.home() / "metadata-db/"
        assert item.text_archive_dir == Path.home() / "metadata-db/archives"
        assert item.text_extracted_dir == Path.home() / "metadata-db/articles"

        Item.DOWNLOAD_DIR = "/data/fulltext"
        assert item.download_dir == Path("/data/fulltext")
        assert item.text_archive_dir == Path("/data/fulltext") / "archives"
        assert item.text_extracted_dir == Path("/data/fulltext") / "articles"
        assert item.title_char_count == 20
        assert item.title_word_count == 5

    # @patchfs
    # def test_is_downloaded(self, fs, item_1894_sep_5: Item) -> None:
    #     item = Item.objects.get(item_code=TEST_ITEM_CODE)
    #     assert item == item_1894_sep_5
    #
    #     assert not item.is_downloaded()
    #
    #     # Use pyfakefs to fake the filesystem and create the archive file.
    #     assert item.text_archive_dir == Path.home() / "metadata-db/archives"
    #     fs.create_dir(item.text_archive_dir)
    #     fs.create_file(
    #         item.text_archive_dir / "0003040_plaintext.zip", contents="dummy"
    #     )
    #
    #     assert item.is_downloaded()

    def test_extract_fulltext(self, item_1894_sep_5: Item):
        item = Item.objects.get(item_code=TEST_ITEM_CODE)
        assert item == item_1894_sep_5
        last_57_chars = "Tile—jUr7 concurred, and returned • verdict accordingly.\n"
        # TODO #24: testing.
        # self.assertEqual(item.fulltext[-57:], last_57_chars)

    def test_sync_title_length(self, item_1894_sep_5: Item, caplog) -> None:
        """Test managing title length."""
        title_extension: str = " LINE"
        test_item = Item.objects.get(item_code=TEST_ITEM_CODE)
        assert test_item == item_1894_sep_5
        assert test_item.title == TEST_ITEM_TITLE
        new_title = TEST_ITEM_TITLE + title_extension
        test_item.title = new_title
        with pytest.raises(Item.TitleLengthError):
            test_item.save(sync_title_counts=False)
        correct_char_count: int = len(new_title)
        correct_word_count: int = word_count(new_title)
        with caplog.at_level(level=DEBUG):
            test_item.save()
        assert test_item.title == new_title[: test_item.MAX_TITLE_CHAR_COUNT]
        assert test_item.title_char_count == correct_char_count
        assert test_item.title_word_count == correct_word_count
        correct_logs: list[str] = [
            (
                f"{MODULE_LOG_PREFIX}482 Setting 'title_char_count' for "
                f"'{TEST_ITEM_CODE}' to {correct_char_count}"
            ),
            (
                f"{MODULE_LOG_PREFIX}502 Setting 'title_word_count' for "
                f"'{TEST_ITEM_CODE}' to {correct_word_count}"
            ),
        ]
        for log in correct_logs:
            assert log in caplog.text
        assert not test_item.title_truncated

    def test_sync_title_length_too_long(self, item_1894_sep_5: Item, caplog) -> None:
        """Test managing title length beyond max characters."""
        if not Item.MAX_TITLE_CHAR_COUNT:
            Item.MAX_TITLE_CHAR_COUNT = settings.DEFAULT_MAX_NEWSPAPER_TITLE_CHAR_COUNT
        max_title_char_count: int = Item.MAX_TITLE_CHAR_COUNT
        title_extension: str = " TOO LONG" * int(
            max_title_char_count / 4
        )  # Ensure longer than MX
        test_item = Item.objects.get(item_code=TEST_ITEM_CODE)
        assert test_item == item_1894_sep_5
        assert test_item.title == TEST_ITEM_TITLE
        new_title = TEST_ITEM_TITLE + title_extension
        test_item.title = new_title
        with pytest.raises(Item.TitleLengthError):
            test_item.save(sync_title_counts=False)
        correct_char_count: int = len(new_title)
        correct_word_count: int = word_count(new_title)
        with caplog.at_level(DEBUG):
            test_item.save()
        assert test_item.title == new_title[:max_title_char_count]
        assert test_item.title_char_count == correct_char_count
        assert test_item.title_word_count == correct_word_count
        correct_logs: list[str] = [
            (
                f"{MODULE_LOG_PREFIX}482 Setting 'title_char_count' for "
                f"'{TEST_ITEM_CODE}' to {correct_char_count}"
            ),
            (
                f"{MODULE_LOG_PREFIX}502 Setting 'title_word_count' for "
                f"'{TEST_ITEM_CODE}' to {correct_word_count}"
            ),
            (
                f"{MODULE_LOG_PREFIX}521 Trimming title of '{TEST_ITEM_CODE}' "
                f"to {test_item.MAX_TITLE_CHAR_COUNT} chars."
            ),
        ]
        for log in correct_logs:
            assert log in caplog.text
        assert test_item.title_truncated
        assert str(test_item) == truncate_str(
            test_item.title, MAX_PRINT_SELF_STR_LENGTH
        )

    def test_sync_title_length_max_title_none(
        self, item_1894_sep_5: Item, caplog
    ) -> None:
        """Test unbound title length `MAX_TITLE_CHAR_COUNT = None`."""
        title_extension: str = " LINE"
        Item.MAX_TITLE_CHAR_COUNT = None
        test_item = Item.objects.get(item_code=TEST_ITEM_CODE)
        assert test_item == item_1894_sep_5
        assert test_item.title == TEST_ITEM_TITLE
        new_title = TEST_ITEM_TITLE + title_extension
        test_item.title = new_title
        with pytest.raises(Item.TitleLengthError):
            test_item.save(sync_title_counts=False)
        test_item.save(sync_title_counts=True)
        correct_char_count: int = len(new_title)
        correct_word_count: int = word_count(new_title)
        with caplog.at_level(DEBUG):
            test_item.save()
        assert test_item.title == new_title
        assert test_item.title_char_count == correct_char_count
        assert test_item.title_word_count == correct_word_count
        correct_logs: list[str] = [
            (
                f"{MODULE_LOG_PREFIX}482 Setting 'title_char_count' for "
                f"'{TEST_ITEM_CODE}' to {correct_char_count}"
            ),
            (
                f"{MODULE_LOG_PREFIX}502 Setting 'title_word_count' for "
                f"'{TEST_ITEM_CODE}' to {correct_word_count}"
            ),
        ]
        for log in correct_logs:
            assert log in caplog.text
        assert test_item.title_truncated is False


@pytest.mark.parametrize(
    "item_code, use_filename_endswith",
    ((TEST_ITEM_CODE, False), ("", True), (None, True), ("wrong", True)),
)
@pytest.mark.django_db
def test_full_text_and_item(
    item_1894_sep_5: Item, item_code: str | None, use_filename_endswith: bool
) -> None:
    """Test creating `FullText` instances and relating to `Item`."""
    full_text_1894_sep_5 = FullText(
        item_code=item_code,
        text_fixture_path="fulltext/fixtures/plaintext_fixture-38884.json",
        text_compressed_path="0003548_plaintext.zip",
        text_path=TEST_ITEM_INPUT_FILENAME,
    )
    full_text_1894_sep_5.save()
    assert not full_text_1894_sep_5.canonical
    assert full_text_1894_sep_5.item is None

    # The `item_code` is returned from `.set_related_item_by_text_path`
    if item_code == "wrong":
        with pytest.raises(FullText.NoMatchingItemCode):
            full_text_1894_sep_5.set_related_item_by_text_path(
                set_canonical=True, use_filename_endswith=use_filename_endswith
            )
    else:
        issue: Issue = full_text_1894_sep_5.set_related_item_by_text_path(
            set_canonical=True, use_filename_endswith=use_filename_endswith
        )
        assert repr(issue) == TEST_ITEM_CODE
        assert full_text_1894_sep_5.canonical
        assert full_text_1894_sep_5.item == item_1894_sep_5
        assert set(item_1894_sep_5.full_texts.all()) == {full_text_1894_sep_5}
        assert item_1894_sep_5.full_text_canonical == full_text_1894_sep_5
