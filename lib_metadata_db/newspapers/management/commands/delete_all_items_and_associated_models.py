from django.core.management import BaseCommand


from lib_metadata_db.newspapers.models.digitisations import Digitisation
from lib_metadata_db.newspapers.models.ingest import Ingest
from lib_metadata_db.newspapers.models.items import Item
from lib_metadata_db.newspapers.models.issues import Issue
from lib_metadata_db.newspapers.models.data_providers import DataProvider
from lib_metadata_db.newspapers.models.publications import Publication


class Command(BaseCommand):
    help = "Delete all model objects associated with the Items models and their foreign keys"

    def handle(self, *args, **options):
        answer = input(
            "Do you want to remove all data associated with the newspapers models? This is a destructive option and should only be done on a production database instance with the approval of the Administrator. Continue? "
        )
        if answer.lower() in ["y", "yes"]:
            Item.objects.all().delete()
            Digitisation.objects.all().delete()
            Ingest.objects.all().delete()
            Issue.objects.all().delete()
            Publication.objects.all().delete()
            DataProvider.objects.all().delete()
            # Do other stuff
        else:
            # Handle "wrong" input
            print("Exiting deletion.")
            pass
