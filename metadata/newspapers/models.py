from pathlib import Path
from zipfile import ZipFile
import os

from django.db import models
from django_pandas.managers import DataFrameManager
from gazetteer.models import Place

from azure.storage.blob import BlobClient


class NewspapersModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = DataFrameManager()

    class Meta:
        abstract = True


class DataProvider(NewspapersModel):
    # TODO #48: Change unique_together to solely unique on name?
    name = models.CharField(max_length=600, default=None)
    collection = models.CharField(max_length=600, default=None)
    source_note = models.CharField(max_length=255, default=None)

    class Meta:
        unique_together = ("name", "collection")

    def __str__(self):
        return str(self.name)


class Digitisation(NewspapersModel):
    # TODO #48: Change unique_together to solely unique on software?
    xml_flavour = models.CharField(max_length=255, default=None)
    software = models.CharField(max_length=600, default=None, null=True, blank=True)
    mets_namespace = models.CharField(
        max_length=255, default=None, blank=True, null=True
    )
    alto_namespace = models.CharField(
        max_length=255, default=None, blank=True, null=True
    )

    class Meta:
        unique_together = ("xml_flavour", "software")

    def __str__(self):
        return f"{self.mets_namespace}, {self.alto_namespace}"


class Ingest(NewspapersModel):
    lwm_tool_name = models.CharField(max_length=600, default=None)
    lwm_tool_version = models.CharField(max_length=600, default=None)
    lwm_tool_source = models.CharField(max_length=255, default=None)

    class Meta:
        unique_together = ("lwm_tool_name", "lwm_tool_version")

    def __str__(self):
        return str(self.lwm_tool_version)


class Newspaper(NewspapersModel):
    # TODO #48: publication_code should be unique, right?
    publication_code = models.CharField(max_length=600, default=None)
    title = models.CharField(max_length=255, default=None)
    location = models.CharField(max_length=255, default=None, blank=True, null=True)
    place_of_publication = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        null=True,
        related_name="newspapers",
        related_query_name="newspaper",
    )

    def __str__(self):
        return str(self.publication_code)


class Issue(NewspapersModel):
    # TODO #48: issue_code should be unique, right?
    issue_code = models.CharField(max_length=600, default=None)
    issue_date = models.DateField()
    input_sub_path = models.CharField(max_length=255, default=None)

    newspaper = models.ForeignKey(
        Newspaper,
        on_delete=models.SET_NULL,
        verbose_name="newspaper",
        null=True,
        related_name="issues",
        related_query_name="issue",
    )

    def __str__(self):
        return str(self.issue_code)

    @property
    def url(self):
        """
        Return a URL similar to:
        https://www.britishnewspaperarchive.co.uk/viewer/BL/0000347/18890102/001/0001

        TODO #48: This will not generate a correct URL if there is no date available.
        """

        return f"https://www.britishnewspaperarchive.co.uk/viewer/BL/{self.newspaper.publication_code}/{str(self.issue_date).replace('-', '')}/001/0001"


class Item(NewspapersModel):
    # TODO #48: item_code should be unique, right?
    # TODO #48: Should we set a max_length on the title field?
    item_code = models.CharField(max_length=600, default=None)
    title = models.TextField(default=None)
    item_type = models.CharField(max_length=600, default=None, blank=True, null=True)
    word_count = models.IntegerField(null=True, db_index=True)
    ocr_quality_mean = models.FloatField(null=True, blank=True)
    ocr_quality_sd = models.FloatField(null=True, blank=True)
    input_filename = models.CharField(max_length=255, default=None)
    issue = models.ForeignKey(
        Issue,
        on_delete=models.SET_NULL,
        verbose_name="issue",
        null=True,
        related_name="items",
        related_query_name="item",
    )
    data_provider = models.ForeignKey(
        DataProvider,
        on_delete=models.SET_NULL,
        verbose_name="data_provider",
        null=True,
        related_name="items",
        related_query_name="item",
    )
    digitisation = models.ForeignKey(
        Digitisation,
        on_delete=models.SET_NULL,
        verbose_name="digitisation",
        null=True,
        related_name="items",
        related_query_name="item",
    )
    ingest = models.ForeignKey(
        Ingest,
        on_delete=models.SET_NULL,
        verbose_name="ingest",
        null=True,
        related_name="items",
        related_query_name="item",
    )

    def save(self, *args, **kwargs):
        # for consistency, we save all item_type in uppercase
        self.item_type = str(self.item_type).upper()
        return super(Item, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.item_code)

    HOME_DIR = Path.home()
    DOWNLOAD_DIR = HOME_DIR / "metadata-db/"
    ARCHIVE_SUBDIR = "archives"
    EXTRACTED_SUBDIR = "articles"
    FULLTEXT_METHOD = "download"
    FULLTEXT_CONTAINER_SUFFIX = "-alto2txt"
    FULLTEXT_CONTAINER_PATH = "plaintext/"
    FULLTEXT_STORAGE_ACCOUNT_URL = "https://alto2txt.blob.core.windows.net"

    SAS_ENV_VARIABLE = "FULLTEXT_SAS_TOKEN"

    @property
    def download_dir(self):
        """Path to the download directory for full text data.

        The DOWNLOAD_DIR class attribute contains the directory under which
        full text data will be stored. Users can change it by typing:
        Item.DOWNLOAD_DIR = "/path/to/wherever/"
        """
        return Path(self.DOWNLOAD_DIR)

    @property
    def text_archive_dir(self):
        """Path to the storage directory for full text archives."""
        return self.download_dir / self.ARCHIVE_SUBDIR

    @property
    def text_extracted_dir(self):
        """Path to the storage directory for extracted full text files."""
        return self.download_dir / self.EXTRACTED_SUBDIR

    @property
    def zip_file(self):
        """Filename of the zip archive containing the full text for this item."""
        return f"{self.issue.newspaper.publication_code}_plaintext.zip"

    @property
    def text_container(self):
        """Azure blob storage container containing the Item full text."""
        return f"{self.data_provider.name}{self.FULLTEXT_CONTAINER_SUFFIX}"

    @property
    def text_path(self):
        """Relative path (including filename) to the full text file
        for this Item, both from the root of the zip archive and
        from the DOWNLOAD_DIR (once downloaded and extracted)."""
        return Path(self.issue.input_sub_path) / self.input_filename

    # Commenting this out as it will fail with the dev on #56 (see branch kallewesterling/issue56).
    # As this will likely not be the first go-to for fulltext access, we can keep it as a method:
    # .extract_fulltext()
    #
    # @property
    # def fulltext(self):
    #     try:
    #         return self.extract_fulltext()
    #     except Exception as ex:
    #         print(ex)

    def is_downloaded(self):
        """Check whether a text archive has already been downloaded."""

        file = self.text_archive_dir / self.zip_file
        if not os.path.exists(file):
            return False
        return os.path.getsize(file) != 0

    def download_zip(self):
        """Download the full text zip archive for this Item from cloud storage."""

        sas_token = os.getenv(self.SAS_ENV_VARIABLE).strip('"')
        if sas_token is None:
            raise KeyError(
                f"The environment variable {self.SAS_ENV_VARIABLE} was not found."
            )

        url = self.FULLTEXT_STORAGE_ACCOUNT_URL
        container = self.text_container
        blob_name = str(Path(self.FULLTEXT_CONTAINER_PATH) / self.zip_file)
        download_file_path = self.text_archive_dir / self.zip_file

        # Make sure the archive download directory exists.
        self.text_archive_dir.mkdir(parents=True, exist_ok=True)

        if not os.path.exists(self.text_archive_dir):
            raise RuntimeError(
                f"Failed to make archive download directory at {self.text_archive_dir}"
            )

        # Download the blob archive.
        try:
            client = BlobClient(
                url, container, blob_name=blob_name, credential=sas_token
            )

            with open(download_file_path, "wb") as download_file:
                download_file.write(client.download_blob().readall())

        except Exception as ex:
            if "status_code" in str(ex):
                print("Zip archive download failed.")
                print(
                    f"Ensure the {self.SAS_ENV_VARIABLE} env variable contains a valid SAS token"
                )

            if os.path.exists(download_file_path):
                if os.path.getsize(download_file_path) == 0:
                    os.remove(download_file_path)
                    print(f"Removing empty download: {download_file_path}")

    def extract_fulltext_file(self):
        """Extract the full text file for this Item from a zip archive
        and store it in under the DOWNLOAD_DIR."""

        archive = self.text_archive_dir / self.zip_file
        with ZipFile(archive, "r") as zip_ref:
            zip_ref.extract(str(self.text_path), path=self.text_extracted_dir)

    def read_fulltext_file(self):
        """Read the full text for this Item from a file."""

        with open(self.text_extracted_dir / self.text_path) as f:
            lines = f.readlines()
        return lines

    def extract_fulltext(self, *args, **kwargs) -> str:
        """Extract the full text of this newspaper item."""

        # If the item full text has already been extracted, read it.
        if os.path.exists(self.text_extracted_dir / self.text_path):
            return self.read_fulltext_file()

        if self.FULLTEXT_METHOD == "download":

            # If not already available locally, download the full text archive.
            if not self.is_downloaded():
                self.download_zip()

            if not self.is_downloaded():
                # TODO: handle more gracefully.
                raise RuntimeError(
                    f"Failed to download full text archive for item {self.item_code}."
                )

            # Extract the text for this item.
            self.extract_fulltext_file()

        elif self.FULLTEXT_METHOD == "blobfuse":

            # TODO: Blobfuse method not yet implemented.

            blobfuse = "/mounted/blob/storage/path/"
            zip_path = blobfuse / self.zip_file

            raise NotImplementedError("Blobfuse access is not yet implemented.")

        else:
            raise RuntimeError(
                "A valid fulltext access method must be selected: options are 'download' or 'blobfuse'."
            )

        # If the item full text still hasn't been extracted, report failure.
        if not os.path.exists(self.text_extracted_dir / self.text_path):
            # TODO: handle more gracefully.
            raise RuntimeError(f"Failed to extract fulltext for {self.item_code}.")

        return self.read_fulltext_file()
