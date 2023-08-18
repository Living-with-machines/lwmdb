from datetime import datetime
from logging import DEBUG
from pathlib import Path
from typing import Final

import pytest
from django.conf import settings
from django.test import TestCase
from pyfakefs.fake_filesystem_unittest import patchfs

from lwmdb.utils import truncate_str, word_count

from .models import MAX_PRINT_SELF_STR_LENGTH, DataProvider, Issue, Item, Newspaper

TEST_ITEM_CODE: Final[str] = "0003040-18940905-art0030"
TEST_ITEM_TITLE: Final[str] = "SAD END OF A RAILWAY"
TEST_ITEM_TITLE_CHAR_COUNT: Final[int] = 20
TEST_ITEM_TITLE_WORD_COUNT: Final[int] = 5

MODULE_LOG_PREFIX: Final[str] = "DEBUG:newspapers.models:"

# @pytest.mark.django_db
# @pytest.mark.fixture
# def test_item(test_code: str = TEST_ITEM_CODE) -> Item:
#     return Item.objects.get(item_code=test_code)


@pytest.mark.django_db
class ItemTestCase(TestCase):
    """Test creating and querying Item, Issue and Newpaper instances."""

    def setUp(self) -> None:
        newspaper = Newspaper.objects.create(
            publication_code="0003040",
            title="The Birkenhead News and Wirral General Advertiser",
        )

        issue = Issue.objects.create(
            issue_code="0003040-18940905",
            issue_date=datetime(year=1894, month=9, day=5),
            input_sub_path="0003040/1894/0905",
            newspaper=newspaper,
        )

        data_provider = DataProvider.objects.create(
            name="lwm", collection="newspapers", source_note=""
        )

        Item.objects.create(
            item_code=TEST_ITEM_CODE,
            title=TEST_ITEM_TITLE,
            input_filename="0003040_18940905_art0030.txt",
            issue=issue,
            data_provider=data_provider,
        )

    def test_item_parameters(self) -> None:
        item = Item.objects.get(item_code="0003040-18940905-art0030")

        self.assertEqual(item.title, TEST_ITEM_TITLE)
        self.assertEqual(item.data_provider.name, "lwm")
        self.assertEqual(item.zip_file, "0003040_plaintext.zip")
        self.assertEqual(
            item.text_path, Path("0003040/1894/0905/0003040_18940905_art0030.txt")
        )
        self.assertEqual(item.text_container, "lwm-alto2txt")

        self.assertEqual(item.download_dir, Path.home() / "metadata-db/")
        self.assertEqual(item.text_archive_dir, Path.home() / "metadata-db/archives")
        self.assertEqual(item.text_extracted_dir, Path.home() / "metadata-db/articles")

        Item.DOWNLOAD_DIR = "/data/fulltext"
        self.assertEqual(item.download_dir, Path("/data/fulltext"))
        self.assertEqual(item.text_archive_dir, Path("/data/fulltext") / "archives")
        self.assertEqual(item.text_extracted_dir, Path("/data/fulltext") / "articles")
        assert item.title_char_count == 20
        assert item.title_word_count == 5

    @patchfs
    def test_is_downloaded(self, fs) -> None:
        item = Item.objects.get(item_code="0003040-18940905-art0030")

        self.assertFalse(item.is_downloaded())

        # Use pyfakefs to fake the filesystem and create the archive file.
        self.assertEqual(item.text_archive_dir, Path.home() / "metadata-db/archives")
        fs.create_dir(item.text_archive_dir)
        fs.create_file(
            item.text_archive_dir / "0003040_plaintext.zip", contents="dummy"
        )

        self.assertTrue(item.is_downloaded())

    def test_extract_fulltext(self):
        item = Item.objects.get(item_code="0003040-18940905-art0030")
        last_57_chars = "Tile—jUr7 concurred, and returned • verdict accordingly.\n"
        # TODO #24: testing.
        # self.assertEqual(item.fulltext[-57:], last_57_chars)

    def test_sync_title_length(self) -> None:
        """Test managing title length."""
        title_extension: str = " LINE"
        test_item = Item.objects.get(item_code=TEST_ITEM_CODE)
        assert test_item.title == TEST_ITEM_TITLE
        new_title = TEST_ITEM_TITLE + title_extension
        test_item.title = new_title
        with pytest.raises(Item.TitleLengthError):
            test_item.save(sync_title_counts=False)
        correct_char_count: int = len(new_title)
        correct_word_count: int = word_count(new_title)
        with self.assertLogs(level=DEBUG) as logs:
            test_item.save()
        assert test_item.title == new_title[: test_item.MAX_TITLE_CHAR_COUNT]
        assert test_item.title_char_count == correct_char_count
        assert test_item.title_word_count == correct_word_count
        correct_logs: list[str] = [
            (
                f"{MODULE_LOG_PREFIX}Setting `title_char_count` for "
                f"{TEST_ITEM_CODE} to {correct_char_count}"
            ),
            (
                f"{MODULE_LOG_PREFIX}Setting `title_word_count` for "
                f"{TEST_ITEM_CODE} to {correct_word_count}"
            ),
        ]
        assert logs.output == correct_logs
        assert not test_item.title_truncated

    def test_sync_title_length_too_long(self) -> None:
        """Test managing title length beyond max characters."""
        if not Item.MAX_TITLE_CHAR_COUNT:
            Item.MAX_TITLE_CHAR_COUNT = settings.DEFAULT_MAX_NEWSPAPER_TITLE_CHAR_COUNT
        max_title_char_count: int = Item.MAX_TITLE_CHAR_COUNT
        title_extension: str = " TOO LONG" * int(
            max_title_char_count / 4
        )  # Ensure longer than MX
        test_item = Item.objects.get(item_code=TEST_ITEM_CODE)
        assert test_item.title == TEST_ITEM_TITLE
        new_title = TEST_ITEM_TITLE + title_extension
        test_item.title = new_title
        with pytest.raises(Item.TitleLengthError):
            test_item.save(sync_title_counts=False)
        correct_char_count: int = len(new_title)
        correct_word_count: int = word_count(new_title)
        with self.assertLogs(level=DEBUG) as logs:
            test_item.save()
        assert test_item.title == new_title[:max_title_char_count]
        assert test_item.title_char_count == correct_char_count
        assert test_item.title_word_count == correct_word_count
        correct_logs: list[str] = [
            (
                f"{MODULE_LOG_PREFIX}Setting `title_char_count` for "
                f"{TEST_ITEM_CODE} to {correct_char_count}"
            ),
            (
                f"{MODULE_LOG_PREFIX}Setting `title_word_count` for "
                f"{TEST_ITEM_CODE} to {correct_word_count}"
            ),
            (
                f"{MODULE_LOG_PREFIX}Trimming title of {TEST_ITEM_CODE} "
                f"to {test_item.MAX_TITLE_CHAR_COUNT} chars."
            ),
        ]
        assert logs.output == correct_logs
        assert test_item.title_truncated
        assert str(test_item) == truncate_str(
            test_item.title, MAX_PRINT_SELF_STR_LENGTH
        )

    def test_sync_title_length_max_title_none(self) -> None:
        """Test unbound title length `MAX_TITLE_CHAR_COUNT = None`."""
        title_extension: str = " LINE"
        Item.MAX_TITLE_CHAR_COUNT = None
        test_item = Item.objects.get(item_code=TEST_ITEM_CODE)
        assert test_item.title == TEST_ITEM_TITLE
        new_title = TEST_ITEM_TITLE + title_extension
        test_item.title = new_title
        with pytest.raises(Item.TitleLengthError):
            test_item.save(sync_title_counts=False)
        test_item.save(sync_title_counts=True)
        correct_char_count: int = len(new_title)
        correct_word_count: int = word_count(new_title)
        with self.assertLogs(level=DEBUG) as logs:
            test_item.save()
        assert test_item.title == new_title
        assert test_item.title_char_count == correct_char_count
        assert test_item.title_word_count == correct_word_count
        correct_logs: list[str] = [
            (
                f"{MODULE_LOG_PREFIX}Setting `title_char_count` for "
                f"{TEST_ITEM_CODE} to {correct_char_count}"
            ),
            (
                f"{MODULE_LOG_PREFIX}Setting `title_word_count` for "
                f"{TEST_ITEM_CODE} to {correct_word_count}"
            ),
        ]
        assert logs.output == correct_logs
        assert test_item.title_truncated is False
