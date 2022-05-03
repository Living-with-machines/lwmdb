from lib_metadata_db.newspapers.models.digitisations import Digitisation
from lib_metadata_db.newspapers.models.ingest import Ingest
from django.core.management import BaseCommand

from lib_metadata_db.newspapers.models.items import Item
from lib_metadata_db.newspapers.models.issues import Issue
from lib_metadata_db.newspapers.models.data_providers import DataProvider
from lib_metadata_db.newspapers.models.publications import Publication

class Command(BaseCommand):
    def handle(self, *args, **options):
        Item.objects.all().delete()
        Digitisation.objects.all().delete()
        Ingest.objects.all().delete()
        Issue.objects.all().delete()
        Publication.objects.all().delete()
        DataProvider.objects.all().delete()