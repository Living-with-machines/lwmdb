import os
from logging import getLogger
from pathlib import Path
from typing import Final, Union
from zipfile import ZipFile

from azure.storage.blob import BlobClient
from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from django_pandas.managers import DataFrameManager

from gazetteer.models import Place
from lwmdb.utils import (
    MAX_PATH_LENGTH,
    DupeFixConfig,
    dupes_to_fix,
    get_unique_record,
    truncate_str,
    word_count,
)

logger = getLogger(__name__)

CODE_SEPERATOR_CHAR: Final[str] = "-"
MAX_PRINT_SELF_STR_LENGTH: Final[int] = 80
NEWSPAPER_ISSUE_ITEM_CODE_MAX_LENGTH: Final[int] = 600


class NewspapersModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = DataFrameManager()

    class Meta:
        abstract = True


class DataProvider(NewspapersModel):
    """Source and collection information for data provider."""

    name = models.CharField(max_length=600, default=None)
    collection = models.CharField(max_length=600, default=None)
    source_note = models.CharField(max_length=255, default=None)
    code = models.SlugField(
        max_length=100, default=None, null=True, blank=True, unique=True
    )
    legacy_code = models.SlugField(
        max_length=100, default=None, null=True, blank=True, unique=True
    )

    class Meta:
        unique_together = [("name", "collection")]

    def __str__(self):
        return truncate_str(self.name, max_length=MAX_PRINT_SELF_STR_LENGTH)


class Digitisation(NewspapersModel):
    """Means by which collection was digitised."""

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
    """Tool used for database ingest."""

    lwm_tool_name = models.CharField(max_length=600, default=None)
    lwm_tool_version = models.CharField(max_length=600, default=None)
    lwm_tool_source = models.CharField(max_length=255, default=None)

    class Meta:
        unique_together = ("lwm_tool_name", "lwm_tool_version")

    def __str__(self):
        return truncate_str(self.lwm_tool_name, max_length=MAX_PRINT_SELF_STR_LENGTH)


class Newspaper(NewspapersModel):
    """Newspaper, including title and place.

    Attributes:
        publication_code:
            a code to uniquely identify each newspaper derived from
        title:
            Newspaper title (assumed to be constant over time)
        location:
            Name of location an instance is associated with
        place_of_publication:
            A `Place` `gazetteer` record an instance is associated with.

    Example:
        ```pycon
        >>> getfixture("db")
        >>> new_tredegar = Newspaper(publication_code="0003548",
        ...                          title=("New Tredegar, "
        ...                                 "Bargoed & Caerphilly Journal"),
        ...                          location="Bedwellty, Gwent, Wales",)
        >>> new_tredegar
        0003548
        >>> str(new_tredegar)
        'New Tredegar, Bargoed & Caerphilly Journal'
        >>> new_tredegar.place_of_publication
        >>> Newspaper.objects.count()
        0
        >>> new_tredegar.save()
        >>> Newspaper.objects.count()
        1

        ```
    """

    # TODO #55: publication_code should be unique? Currently unique (
    #                           but not tested with BNA)
    publication_code = models.CharField(
        max_length=NEWSPAPER_ISSUE_ITEM_CODE_MAX_LENGTH, default=None
    )
    title = models.CharField(max_length=255, default=None)
    location = models.CharField(max_length=255, default=None, blank=True, null=True)
    place_of_publication = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        null=True,
        related_name="newspapers",
        related_query_name="newspaper",
    )

    def __repr__(self):
        return self.publication_code

    def __str__(self):
        return truncate_str(self.title, max_length=MAX_PRINT_SELF_STR_LENGTH)

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "publication_code",
                ]
            )
        ]

    @classmethod
    def dupe_pub_codes_manager(cls) -> DupeFixConfig:
        """Return a `DupeFixConfig` of potential duplicate records."""
        return dupes_to_fix(
            qs_or_model=cls,
            dupe_fields=("publication_code", "title"),
            dupe_method_kwargs={"null_relations": ("issue",)},
        )


class Issue(NewspapersModel):
    """Newspaper Issue, including date and relevant source url.

    Attributes:
        issue_code:
            A `str` of form:

            ```
            {newspaper.publication_code}-{issue.issue_date.strftime('%Y%m%d')}
            ```

            For example: if

            * `newspaper.publication_code` is `0000347`
            * `issue_date` is `datetime.date(1904, 7, 7)`

            then the `issue_code` is

            ```
            0003548-19040707
            ```

            These codes are designed to uniquely identify each issue, at
            least with respect to each related `Newspaper`.

            !!! note

                See tickets [#55](https://github.com/Living-with-machines/lwmdb/issues/55)
                and [#93](https://github.com/Living-with-machines/lwmdb/issues/55)
                for updates on ensuring uniqueness.
        issue_date:
            Date of issue publication.
        input_sub_path:
            A `str` to convert into a path for related source OCR files.
            See [`Item.text_path`][Item.text_path]
        newspaper:
            `Newspaper` record each `Issue` is from.

    Example:
        ```pycon
        >>> getfixture("db")
        >>> from datetime import date
        >>> new_tredegar = Newspaper(publication_code="0003548",
        ...                          title=("New Tredegar, "
        ...                                 "Bargoed & Caerphilly Journal"),
        ...                          location="Bedwellty, Gwent, Wales",)
        >>> issue = Issue(issue_code="0003548-19040707",
        ...               issue_date=date(1904, 7, 7),
        ...               newspaper=new_tredegar,
        ...               input_sub_path='0003548/1904/0707')
        >>> print(issue)
        0003548-19040707
        >>> issue.issue_date
        datetime.date(1904, 7, 7)
        >>> new_tredegar.save()
        >>> Issue.objects.count()
        0
        >>> issue.save()
        >>> Issue.objects.count()
        1

        ```
    """

    # TODO #55: issue_code should be unique? Currently unique (but not tested with BNA)
    issue_code = models.CharField(
        max_length=NEWSPAPER_ISSUE_ITEM_CODE_MAX_LENGTH, default=None
    )
    issue_date = models.DateField()
    input_sub_path = models.CharField(max_length=MAX_PATH_LENGTH, default=None)

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
        """Return a URL similar to the British Newspaper Archive structure.

        Example:
            https://www.britishnewspaperarchive.co.uk/viewer/BL/0000347/18890102/001/0001
        """
        if not self.issue_date:
            print("Warning: No date available for issue so URL will likely not work.")

        return (
            f"https://www.britishnewspaperarchive.co.uk/viewer/BL/"
            f"{self.newspaper.publication_code}/"
            f"{str(self.issue_date).replace(CODE_SEPERATOR_CHAR, '')}/001/0001"
        )

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "issue_code",
                ]
            )
        ]


class Item(NewspapersModel):
    """Printed element in a Newspaper issue including metadata.

    Attributes:
        MAX_TITLE_CHAR_COUNT:
            Maximum length for `Item` title field. The default set by
            `settings.MAX_NEWSPAPER_TITLE_CHAR_COUNT`, which can be
            customised in `.env`. This can also be `None`, in which
            case there is no maximum enforced beyond `postgres`
            [spec](https://www.postgresql.org/docs/current/datatype-character.html).

            !!! note

                This is not stored in SQL, only within the class.

        item_code:
            A unique code for each `Item` of the form:
            ```
            {newspaper.publication_code}-{issue.issue_code}-{item.item_code}
            ```

            For example:
                - the 37th `Item` in
                - `Issue` on 7 July 1904 from
                - _New Tredegar_ (`publication_code` `0003548`)

            will have an `item_code`:
                ```
                0003548-19040707-art0037`
                ```

            !!! note

                The `art` prefix on the last portion of the `item_code` may vary
                by newspaper collection

        title:
            Item title. If `truncation` is applied and the original title
            is longer than `MAX_NEWSPAPER_TITLE_CHAR_COUNT`, this is the
            title up to the truncation point, followed by
            [`lwmdb.utils.DEFFAULT_TRUNCATION_CHARS`][lwmdb.utils.DEFFAULT_TRUNCATION_CHARS]

        title_word_count:
            Number of words in the title, prior to any truncation, assuming
            English sentence structure.

        title_char_count:
            Number of characters in the title prior to any truncation.

        title_truncated:
            Whether the `title` field has been truncated. If `None`,
            then the title length has not had truncation process applied.

        item_type:
            What time of item. By default all capps. Known types
            include ARTICLE and ADVERT.
            Todo: This needs fleshing out.

        word_count:
            Word count of `FullText` body text
            (assuming English sentence structure).

        word_char_count:
            The number of characters in the `FullText` body text.

        ocr_quality_sd:
            Standard deviation of Optical Character Recognition quality scores.

        ocr_quality_mean:
            Mean of Optical Character Recognition quality scores.

        input_filename:
            Filename of `FullText`.

        issue:
            Related `Newspaper` `Issue` record.

        data_provider:
            Related record of newspaper data provider in `DataProvider.

        digitisation:
            Related record of means collection was digitised in `Digitisation`.

        ingest:
            Related tool used for database ingest, including version in `Ingest`.

        full_text:
            Related record of `item` plain text in `FullText`.

    Example:
        ```pycon
        >>> getfixture("db")
        >>> lwm_data_provider = getfixture('lwm_data_provider')
        Installed 5 object(s) from 1 fixture(s)
        >>> new_tredegar = Newspaper(
        ...     publication_code="0003548",
        ...     title=("New Tredegar, "
        ...            "Bargoed & Caerphilly Journal"),
        ...     location="Bedwellty, Gwent, Wales",)
        >>> issue = Issue(issue_code="0003548-19040707",
        ...     issue_date="1904-7-7",
        ...     input_sub_path='0003548/1904/0707',
        ...     newspaper=new_tredegar,)
        >>> item = Item(
        ...     item_code="0003548-19040707-art0037",
        ...     title='MEETING AT CAERPHILLY.',
        ...     item_type="ARTICLE",
        ...     ocr_quality_mean=0.8526,
        ...     ocr_quality_sd=0.2192,
        ...     input_filename='0003548_19040707_art0037.txt',
        ...     issue=issue,
        ...     word_count=1261,
        ...     data_provider=lwm_data_provider)
        >>> item
        0003548-19040707-art0037
        >>> str(item)
        'MEETING AT CAERPHILLY.'
        >>> item.word_count
        1261
        >>> item.title_word_count
        >>> item.title_char_count
        >>> item.title_truncated
        >>> new_tredegar.save()
        >>> issue.save()
        >>> item.save()  # This calls `item._sync_title_counts()`
        >>> item.title_word_count
        3
        >>> item.title_char_count
        22
        >>> item.title_truncated
        False

        ```
    """

    # TODO #55: item_code should be unique? Currently, not unique, however so needs fixing in alto2txt2fixture
    MAX_TITLE_CHAR_COUNT: int | None = settings.MAX_NEWSPAPER_TITLE_CHAR_COUNT

    item_code = models.CharField(
        max_length=NEWSPAPER_ISSUE_ITEM_CODE_MAX_LENGTH, default=None
    )
    title = models.TextField(max_length=MAX_TITLE_CHAR_COUNT, default=None)
    title_word_count = models.IntegerField(null=True)
    title_char_count = models.IntegerField(null=True)
    title_truncated = models.BooleanField(default=None, null=True, blank=True)
    item_type = models.CharField(max_length=600, default=None, blank=True, null=True)
    word_count = models.IntegerField(null=True, db_index=True)
    word_char_count = models.IntegerField(null=True)
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

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "item_code",
                ]
            )
        ]

    def save(self, sync_title_counts: bool = True, *args, **kwargs):
        # for consistency, we save all item_type in uppercase
        self.item_type = str(self.item_type).upper()
        self._sync_title_counts(force=sync_title_counts)
        return super().save(*args, **kwargs)

    def __str__(self):
        return truncate_str(self.title, max_length=MAX_PRINT_SELF_STR_LENGTH)

    def __repr__(self):
        return str(self.item_code)

    def _sync_title_char_count(self, force: bool = False) -> None:
        title_text_char_count: int = len(self.title)
        if not self.title_char_count or force:
            logger.debug(
                f"Setting 'title_char_count' for '{self.item_code}' "
                f"to {title_text_char_count}"
            )
            self.title_char_count = title_text_char_count
        else:
            if self.title_char_count != title_text_char_count:
                if (
                    self.MAX_TITLE_CHAR_COUNT
                    and self.title_char_count < self.MAX_TITLE_CHAR_COUNT
                ):
                    raise self.TitleLengthError(
                        f"{self.title_char_count} characters does not "
                        f"equal {title_text_char_count}: the length of "
                        f"title of '{self.item_code}'"
                    )

    def _sync_title_word_count(self, force: bool = False) -> None:
        title_text_word_count: int = word_count(self.title)
        if not self.title_word_count or force:
            logger.debug(
                f"Setting 'title_word_count' for '{self.item_code}' to {title_text_word_count}"
            )
            self.title_word_count = title_text_word_count
        else:
            if self.title_word_count != title_text_word_count:
                raise self.TitleLengthError(
                    f"{self.title_word_count} does not equal {title_text_word_count}: the length of words in title of {self}"
                )

    def _sync_title_counts(self, force: bool = False) -> None:
        """Run '_sync' methods, then trim title if long."""
        self._sync_title_char_count(force=force)
        self._sync_title_word_count(force=force)
        if (
            self.MAX_TITLE_CHAR_COUNT
            and self.title_char_count
            and self.title_char_count > self.MAX_TITLE_CHAR_COUNT
        ):
            logger.debug(
                f"Trimming title of '{self.item_code}' to {self.MAX_TITLE_CHAR_COUNT} chars."
            )
            self.title = self.title[: self.MAX_TITLE_CHAR_COUNT]
            self.title_truncated = True
        else:
            self.title_truncated = False

    HOME_DIR = Path.home()
    DOWNLOAD_DIR = HOME_DIR / "metadata-db/"
    ARCHIVE_SUBDIR = "archives"
    EXTRACTED_SUBDIR = "articles"
    FULLTEXT_METHOD = "download"
    FULLTEXT_CONTAINER_SUFFIX = "-alto2txt"
    FULLTEXT_CONTAINER_PATH = "plaintext/"
    FULLTEXT_STORAGE_ACCOUNT_URL = "https://alto2txt.blob.core.windows.net"

    SAS_ENV_VARIABLE = "FULLTEXT_SAS_TOKEN"

    class TitleLengthError(Exception):
        ...

    @property
    def download_dir(self):
        """Path to the download directory for full text data.

        The `DOWNLOAD_DIR` attribute contains the directory under
        which full text data will be stored. Users can change it by
        setting `Item.DOWNLOAD_DIR = "/path/to/wherever/"`
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
        """Filename for this Item's zip archive containing the full text."""
        return f"{self.issue.newspaper.publication_code}_plaintext.zip"

    @property
    def text_container(self):
        """Azure blob storage container containing the Item full text."""
        return f"{self.data_provider.name}{self.FULLTEXT_CONTAINER_SUFFIX}"

    @property
    def text_path(self):
        """Return a path relative to the full text file for this Item.

        This is generated from the zip archive (once downloaded and
        extracted) from the `DOWNLOAD_DIR` and the filename.
        """
        return Path(self.issue.input_sub_path) / self.input_filename

    @property
    def full_text_canonical(self) -> Union["FullText", None]:
        """If a related `FullText` is marked `canonical` return, else None."""
        query = self.full_texts.filter(canonical=True).distinct()
        if len(query) == 1:
            return query[0]
        elif len(query) > 1:
            raise FullText.DuplicateFullTextError(
                f"{len(query)} related 'FullText' entries "
                f"marked 'canonical', sould be maximum 1 for {self}. "
            )
        else:
            return None

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
        """Download this Item's full text zip archive from cloud storage."""
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

    def extract_full_text_file(self):
        """Extract Item's full text file from a zip archive to DOWNLOAD_DIR."""
        archive = self.text_archive_dir / self.zip_file
        with ZipFile(archive, "r") as zip_ref:
            zip_ref.extract(str(self.text_path), path=self.text_extracted_dir)

    def read_full_text_file(self) -> list[str]:
        """Read the full text for this Item from a file."""
        with open(self.text_extracted_dir / self.text_path) as f:
            lines = f.readlines()
        return lines

    def extract_full_text(self) -> list[str]:
        """Extract the full text of this newspaper item."""
        # If the item full text has already been extracted, read it.
        if os.path.exists(self.text_extracted_dir / self.text_path):
            return self.read_full_text_file()

        if self.FULLTEXT_METHOD == "download":
            # If not already available locally, download the full text archive.
            if not self.is_downloaded():
                self.download_zip()

            if not self.is_downloaded():
                raise RuntimeError(
                    f"Failed to download full text archive for item {self.item_code}: Expected finished download."
                )

            # Extract the text for this item.
            self.extract_full_text_file()

        elif self.FULLTEXT_METHOD == "blobfuse":
            raise NotImplementedError("Blobfuse access is not yet implemented.")
            blobfuse = "/mounted/blob/storage/path/"
            zip_path = blobfuse / self.zip_file

        else:
            raise RuntimeError(
                "A valid full_text access method must be selected: options are 'download' or 'blobfuse'."
            )

        # If the item full text still hasn't been extracted, report failure.
        if not os.path.exists(self.text_extracted_dir / self.text_path):
            raise RuntimeError(
                f"Failed to extract full_text for {self.item_code}; path does not exist: {self.text_extracted_dir / self.text_path}"
            )

        return self.read_full_text_file()


class FullText(NewspapersModel):
    """Optical Charater Recognition newspaper `Item` body text.

    Attributes:
        text: Plain text of `Item`, potentially quite large newspaper
            articles. May have unusual or unreadable sequences of
            characters due to issues with Optical Character Recognition
            quality.
        text_path: path to `plaintext` (`txt`) source file (if used). If
            `self.compressed_path` is set, then `text_path` is to relevant
            `txt` file when `self.text_compressed_path` is uncompressed
        text_compressed_path: path to zip file  (if used).
        text_fixute_path: if `self` is loaded via a `fixture` (likely
            generated by `alto2txt2fixture` in `json` format), the path
            to that fixture file.
        info:  # noqa: D410,D405,D214,D411
            Further information about the text, eg. configuration for new
            OCR method.
        errors:
            `str` records of any logged errors generating this `FullText`.
        created_at:
            date and time the record is created. This can also be
            provided by a fixture, for example via `alto2txt2fixture`
        updated_at:
            date and time the record is last updated. This can also
            be provided by a fixture, example via `alto2txt2fixture`.
            This can help keep track of the timing of any changes
            after, for example, an import from an `alto2txt2fixture`
            `json` fixture file.

    Example:
        ```pycon
        >>> getfixture("db")
        >>> item_full_text = FullText(
        ...     item_code='0003548-19040707-art0037',
        ...     text_fixture_path='fulltext/fixtures/plaintext_fixture-38884.json',
        ...     text_compressed_path='0003548_plaintext.zip',
        ...     text_path='0003548/1904/0707/0003548_19040707_art0037.txt',
        ... )
        >>> item_full_text.save()
        >>> item_full_text.canonical
        False
        >>> item_full_text.item is None
        True
        >>> new_tredegar_item: Item = getfixture(
        ...     "new_tredegar_last_issue_first_item")
        Installed 5 object(s) from 1 fixture(s)
        >>> item_full_text.set_related_item(set_canonical=True)
        0003548-19040707-art0037
        >>> (set(new_tredegar_item.full_texts.all()) ==
        ...  set((item_full_text,)))
        True
        >>> item_full_text.canonical
        True

        ```
    """

    text = models.TextField()
    item = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        verbose_name="Full Text",
        blank=True,
        null=True,
        related_name="full_texts",
        related_query_name="full_text",
    )
    item_code = models.CharField(
        max_length=NEWSPAPER_ISSUE_ITEM_CODE_MAX_LENGTH, blank=True, null=True
    )
    text_path = models.CharField(max_length=MAX_PATH_LENGTH, blank=True, null=True)
    text_compressed_path = models.CharField(
        max_length=MAX_PATH_LENGTH, blank=True, null=True
    )
    text_fixture_path = models.CharField(
        max_length=MAX_PATH_LENGTH, blank=True, null=True
    )
    errors = models.TextField(blank=True, null=True)
    info = models.TextField(blank=True, null=True)
    canonical = models.BooleanField(default=False)

    @property
    def file_name(self) -> str:
        """If `self.text_path`, infer file name, else return ''."""
        return Path(self.text_path).name if self.text_path else ""

    def set_canonical(self):
        if not self.canonical and self.item and self.item.full_texts.count() == 1:
            self.canonical = True
            self.save()

    def set_related_item(
        self,
        set_canonical: bool = False,
        use_filename_endswith: bool = False,
        skip_exceptions: bool = False,
    ) -> Item | None:
        """Check and set related `Item` instance by `item_code` or `text_path`.

        Following the conventions that `Item.item_code` and `Item.input_filename`
        should match `text_code` and `text_path` fields exported by
        `alto2txt2fixture`, this function queries `Newspaper.Item` records for
        matches, and if successful sets that relation and returns that `Item`
        instance.

        Args:
            set_canonical:
                Run `self.set_canonical` if related `Item` found.
            use_filename_endswith:
                If `self.item_code` is not set, search for related `Items`
                    with a similar `file_name` that ends with `self.file_name`.
            skip_exceptions: Log `errors` instead of Raise assertions.
        """
        item_obj_or_qs: Item | QuerySet
        if self.text_path:
            if self.item_code:
                item_obj_or_qs = get_unique_record(
                    Item.objects.all(),
                    skip_exceptions=skip_exceptions,
                    item_code=self.item_code,
                )
                if isinstance(item_obj_or_qs, Item):
                    self.item = item_obj_or_qs
            elif use_filename_endswith:
                item_obj_or_qs = get_unique_record(
                    Item.objects.all(),
                    skip_exceptions=skip_exceptions,
                    input_filename__endswith=self.file_name,
                )
                if isinstance(item_obj_or_qs, Item):
                    self.item = item_obj_or_qs
                    self.item_code = self.item.item_code
                elif len(item_obj_or_qs) > 1:
                    raise self.DuplicateFullTextError(
                        f"{len(item_obj_or_qs)} newspaper Items should have exactly 1 "
                        f"FullText from 'text_path' {self.text_path} "
                    )
            else:
                logger.warning(f"No matching 'Newspaper.Item' found for {self}")
                return None
            self.save()
            if set_canonical:
                self.set_canonical()
            return self.item
        return None

    class DuplicateFullTextError(Exception):
        ...

    class DuplicateCanonicalError(Exception):
        ...

    class NoMatchingItemCode(Exception):
        ...
