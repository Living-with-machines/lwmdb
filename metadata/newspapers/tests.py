from datetime import datetime
from django.test import TestCase
from pathlib import Path
from os import environ, getenv
from unittest import mock
from unittest.mock import patch
from pyfakefs.fake_filesystem_unittest import patchfs
from newspapers.models import Newspaper, Issue, Item, DataProvider
from gazetteer.models import Place

# Create your tests here.
class ItemTestCase(TestCase):

    def setUp(self):

        newspaper = Newspaper.objects.create(
            publication_code="0003040",
            title="The Birkenhead News and Wirral General Advertiser"
        )

        issue = Issue.objects.create(
            issue_code="0003040-18940905",
            issue_date=datetime(year=1894, month=9, day=5),
            input_sub_path="0003040/1894/0905",
            newspaper=newspaper
        )

        data_provider = DataProvider.objects.create(
            name="lwm",
            collection="newspapers",
            source_note=""
        )

        item = Item.objects.create(
            item_code="0003040-18940905-art0030",
            title="SAD END OF A RAILWAY",
            input_filename="0003040_18940905_art0030.txt",
            issue=issue,
            data_provider=data_provider
        )

    @mock.patch.dict(environ, {"FULLTEXT_DOWNLOAD_DIR": "/data/fulltext" })
    def test_item_parameters(self):
        
        item = Item.objects.get(item_code="0003040-18940905-art0030")

        self.assertEqual(item.title, "SAD END OF A RAILWAY")
        self.assertEqual(item.data_provider.name, "lwm")
        self.assertEqual(item.zip_file, "0003040_plaintext.zip")
        self.assertEqual(item.text_path, Path("0003040/1894/0905/0003040_18940905_art0030.txt"))
        self.assertEqual(item.text_container, "lwm-alto2txt")

        self.assertEqual(item.download_dir, Path("/data/fulltext/"))
        self.assertEqual(item.text_archive_dir, Path("/data/fulltext/archives"))
        self.assertEqual(item.text_extracted_dir, Path("/data/fulltext/articles"))


    @patchfs
    @mock.patch.dict(environ, {"FULLTEXT_DOWNLOAD_DIR": "/data/fulltext" })
    def test_is_downloaded(self, fs):

        item = Item.objects.get(item_code="0003040-18940905-art0030")
        self.assertFalse(item.is_downloaded())

        # Use pyfakefs to fake the filesystem and create the archive file.
        fs.create_dir('/data/fulltext/archives/')
        fs.create_file('/data/fulltext/archives/0003040_plaintext.zip', contents="dummy")

        self.assertTrue(item.is_downloaded())

    def test_extract_fulltext(self):

        item = Item.objects.get(item_code="0003040-18940905-art0030")
        last_57_chars = "Tile—jUr7 concurred, and returned • verdict accordingly.\n"
        # TODO.
        # self.assertEqual(item.fulltext[-57:], last_57_chars)
