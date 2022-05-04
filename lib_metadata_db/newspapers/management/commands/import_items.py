#!/usr/bin/env python3
from bs4 import BeautifulSoup

from django.core.management import BaseCommand
from lib_metadata_db.newspapers.models.digitisations import Digitisation
from lib_metadata_db.newspapers.models.ingest import Ingest

from lib_metadata_db.newspapers.models.items import Item
from lib_metadata_db.newspapers.models.issues import Issue
from lib_metadata_db.newspapers.models.data_providers import DataProvider
from lib_metadata_db.newspapers.models.publications import Publication

from glob import glob

ALREDY_LOADED_ERROR_MESSAGE = """
If you need to reload the item from the XML file,
first delete the db.sqlite3 file to destroy the database.
Then, run `python manage.py migrate` for a new empty
database with tables"""

# Set path to directory where your metadata blob (alto2txt-ed) is mounted.
fullpath = input("Enter full path to to the directory where the metadata is stored: ")
data_provider_name = input(
    "Provide one name for data_provider: (lwm, hmd, bna, jisc): "
)
alltitles = glob("{}/*".format(fullpath))


class Command(BaseCommand):
    def handle(self, *args, **options):
        if Item.objects.exists():
            print("items data already loaded...exiting.")
            print(ALREDY_LOADED_ERROR_MESSAGE)
            return
        # Show this before loading the data into the database
        print("Loading items data")
        # Code to load the data into database
        for each_title in alltitles:
            allyears = glob("{}/*".format(each_title))
            for year in allyears:
                allissues = glob("{}/*".format(year))
                for issue in allissues:
                    metadataxmls = glob("{}/*.xml".format(issue))
                    for metadataxml in metadataxmls:
                        with open(metadataxml, "r") as meta:
                            soup = BeautifulSoup(meta, features="xml")
                            pubmeta = soup.find("publication")
                            processmeta = soup.find("process")
                            issuemeta = pubmeta.find("issue")
                            lwm_tool = processmeta.find("lwm_tool")
                            itemmeta = issuemeta.find("item")
                            publication = Publication(
                                publication_code=pubmeta.get("id"),
                                title=pubmeta.find("title").text,
                                location=pubmeta.find("location").text,
                            )
                            publication.save()
                            issue = Issue(
                                issue_code=issuemeta.get("id"),
                                issue_date=issuemeta.find("date").text,
                                input_sub_path=processmeta.find("input_sub_path").text,
                                publication=publication,
                            )
                            issue.save()
                            data_provider = DataProvider(
                                name=data_provider_name,
                                collection="newspapers",
                                source_note=pubmeta.find("source").text,
                            )
                            data_provider.save()
                            digitisation = Digitisation(
                                xml_flavour=processmeta.find("xml_flavour").text,
                                software=processmeta.find("software").text,
                                mets_namespace=processmeta.find("mets_namespace").text,
                                alto_namespace=processmeta.find("alto_namespace").text,
                            )
                            digitisation.save()
                            ingest = Ingest(
                                lwm_tool_name=lwm_tool.find("name").text,
                                lwm_tool_version=lwm_tool.find("version").text,
                                lwm_tool_source=lwm_tool.find("source").text,
                            )
                            ingest.save()
                            item = Item(
                                item_code=itemmeta.get("id"),
                                title=itemmeta.find("title").text,
                                item_type=itemmeta.find("item_type").text,
                                word_count=itemmeta.find("word_count").text,
                                ocr_quality_mean=itemmeta.find("ocr_quality_mean").text or None,
                                ocr_quality_sd=itemmeta.find("ocr_quality_sd").text or None,
                                input_filename=itemmeta.find("plain_text_file").text,
                                issue=issue,
                                data_provider=data_provider,
                                digitisation=digitisation,
                                ingest=ingest,
                            )
                            item.save()
