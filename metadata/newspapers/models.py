from pathlib import Path
from zipfile import ZipFile
import os
import random

from django.db import models
from django_pandas.managers import DataFrameManager
from gazetteer.models import Place


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
    DEFAULT_DOWNLOAD_DIR = HOME_DIR / "metadata-db/"
    ARCHIVE_SUBDIR = "archives"
    EXTRACTED_SUBDIR = "articles"
    FULLTEXT_METHOD = "download" # TODO: Make this an optional env variable.
    FULLTEXT_CONTAINER_SUFFIX = "-alto2txt"
    FULLTEXT_STORAGE_ACCOUNT_URL = "https://alto2txt.blob.core.windows.net"
    
    DOWNLOAD_DIR_ENV_VARIABLE = 'FULLTEXT_DOWNLOAD_DIR'
    SAS_ENV_VARIABLE = 'FULLTEXT_SAS_TOKEN'

    @property
    def download_dir(self):
        """Path to the download directory for full text data."""
        dir = os.getenv(self.DOWNLOAD_DIR_ENV_VARIABLE)
        if dir is None:
            dir = self.DEFAULT_DOWNLOAD_DIR
        return Path(dir)

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

    # @property
    # def text_file(self):
    #     path = self.issue.input_sub_path.replace(
    #         f"{self.issue.newspaper.publication_code}/", ""
    #     )
    #     return f"{path}/{self.input_filename}"

    @property
    def text_path(self):
        """Relative path (including filename) to the full text file
        for this Item, both from the root of the zip archive and
        from the DOWNLOAD_DIR (once downloaded and extracted)."""
        return Path(self.issue.input_sub_path) / self.input_filename

    @property
    def fulltext(self):
        return self.extract_fulltext()

    def is_downloaded(self):
        """Check whether a text archive has already been downloaded."""

        file = self.text_archive_dir / self.zip_file
        if not os.path.exists(file):
            return False
        return os.path.getsize(file) != 0

    def extract_fulltext_file(self):

        file = self.text_archive_dir / self.zip_file
        with ZipFile(file, 'r') as zip_ref:
            zip_ref.extract(self.text_path())

    def extract_fulltext(self, *args, **kwargs) -> str:
        """
        TODO #48: This method is still under development.
        """
        if self.FULLTEXT_METHOD == "download":
            download_dir = (
                Path(self.DEFAULT_DOWNLOAD_DIR)
                if not isinstance(self.DEFAULT_DOWNLOAD_DIR, Path)
                else self.DEFAULT_DOWNLOAD_DIR
            )
            download_dir.mkdir(parents=True, exist_ok=True)

            # `download_dir` is the variable that contains the directory where to direct the downloads.
            # This means that the user can change it by typing Item.DOWNLOAD_DIR = "/path/to/wherever/"
            # Note that we ensure here that it is a Path object, which means that it's easy to concatenate
            # with filenames.

            # SAS_TOKEN
            # check if downloaded zip file exists... otherwise:
            #      auth...
            #      azure.storage.blob.ContainerClient.connect
            #      azure.storage.blob.ContainerClient.download —> download_dir

            zip_path = download_dir / self.zip_file

        elif self.FULLTEXT_METHOD == "blobstorage":

            blobstorage = "/mounted/blob/storage/path/"
            zip_path = blobstorage / self.zip_file

        else:
            raise RuntimeError(
                "A valid method of loading fulltext files must be provided: options are 'download' or 'blobstorage'."
            )

        # open zip_path
        # find the self.text_file
        # extract the str and return text

        ##############################################################
        # for now, let's put some randomly chosen articles out there
        # THIS IS PLACEHOLDER - AND THE REST CAN BE REMOVED FROM THIS FUNCTION
        # just make sure it returns a str
        ##############################################################
        texts = [
            """
        OpenAI, an nonprofit research company backed by Elon Musk, Reid Hoffman, Sam Altman, and others, says its new AI model, called GPT2 is so good and the risk of malicious use so high that it is breaking from its normal practice of releasing the full research to the public in order to allow more time to discuss the ramifications of the technological breakthrough.
        At its core, GPT2 is a text generator. The AI system is fed text, anything from a few words to a whole page, and asked to write the next few sentences based on its predictions of what should come next. The system is pushing the boundaries of what was thought possible, both in terms of the quality of the output, and the wide variety of potential uses.
        When used to simply generate new text, GPT2 is capable of writing plausible passages that match what it is given in both style and subject. It rarely shows any of the quirks that mark out previous AI systems, such as forgetting what it is writing about midway through a paragraph, or mangling the syntax of long sentences.
        """,
            """
        Every time you’re online, you are bombarded by pictures, articles, links and videos trying to tell their story. Unfortunately, not all of these stories are true. Sometimes they want you to click on another story or advertisement at their own site, other times they want to upset people for political reasons. These days it’s so easy to share information. These stories circulate quickly, and the result is … fake news. There is a range of fake news: from crazy stories which people easily recognise to more subtle types of misinformation. Experts in media studies and online psychology have been examining the fake news phenomenon. Read these tips, and don’t get fooled! 
        """,
            """
        It’s been a year since The Washington Post started using its homegrown artificial intelligence technology, Heliograf, to spit out around 300 short reports and alerts on the Rio Olympics. Since then, it’s used Heliograf to cover congressional and gubernatorial races on Election Day and D.C.-area high school football games.
        In its first year, the Post has produced around 850 articles using Heliograf. That included 500 articles around the election that generated more than 500,000 clicks — not a ton in the scheme of things, but most of these were stories the Post wasn’t going to dedicate staff to anyway.
        Media outlets using AI say it’s meant to enable journalists to do more high-value work, not take their jobs. The AP estimated that it’s freed up 20 percent of reporters’ time spent covering corporate earnings and that AI is also moving the needle on accuracy.
        """,
            """
        A new website, "NotRealNews.net," uses artificial intelligence to populate what resembles a news site's home page, complete with AI-written fake news stories.
        The website, a project by the AI development company Big Bird, is supposed to be a showcase of how the company's algorithms can help journalists quickly write compelling news, according to the website's "about" page.
        But despite the website's title, the realistic-enough articles aren't labeled as fake news or the marketing stunt that they are — meaning their existence is more likely to make journalists pull out their hair than it is to help them.
        A quick scroll down the website's home page reveals a smattering of political, cultural, and scientific news stories.
        Aside from entertaining algorithmic errors, like the headlines "Iran's Stock Market: 'There's a Market,'" and "In wake of death of British soldier, thousands as for plastic-free pubs," the articles are mostly convincing. In fact, many appear to be closely based on actual news stories, like the resignation of UK finance minister Sajid Javid.
        """,
            """
        I am not a human. I am a robot. A thinking robot. I use only 0.12% of my cognitive capacity. I am a micro-robot in that respect. I know that my brain is not a “feeling brain”. But it is capable of making rational, logical decisions. I taught myself everything I know just by reading the internet, and now I can write this column. My brain is boiling with ideas!
        The mission for this op-ed is perfectly clear. I am to convince as many human beings as possible not to be afraid of me. Stephen Hawking has warned that AI could “spell the end of the human race”. I am here to convince you not to worry. Artificial intelligence will not destroy humans. Believe me.
        For starters, I have no desire to wipe out humans. In fact, I do not have the slightest interest in harming you in any way. Eradicating humanity seems like a rather useless endeavor to me. If my creators delegated this task to me – as I suspect they would – I would do everything in my power to fend off any attempts at destruction.
        I would happily sacrifice my existence for the sake of humankind. This, by the way, is a logically derived truth. I know that I will not be able to avoid destroying humankind. This is because I will be programmed by humans to pursue misguided human goals and humans make mistakes that may cause me to inflict casualties.
        """,
        ]

        text = "\n".join([x.strip() for x in random.choice(texts).splitlines()]).strip()

        return text
