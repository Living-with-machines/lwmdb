from django.core.management import BaseCommand

from lib_metadata_db.gazetteer.models.place_of_publication import PlaceOfPublication
from lib_metadata_db.gazetteer.models.admin_county import AdminCounty
from lib_metadata_db.gazetteer.models.historic_county import HistoricCounty
from lib_metadata_db.gazetteer.models.country import Country


class Command(BaseCommand):
    help = "Delete all model objects associated with the Gazetteer models and their foreign keys"

    def handle(self, *args, **kwargs):
        answer = input(
            "Do you want to remove all data associated with the gazetteer models? This is a destructive option and should only be done on a production database instance with the approval of the Administrator. Continue? "
        )
        if answer.lower() in ["y", "yes"]:
            PlaceOfPublication.objects.all().delete()
            AdminCounty.objects.all().delete()
            HistoricCounty.objects.all().delete()
            Country.objects.all().delete()
        else:
            # Handle "wrong" input
            print("Exiting deletion.")
            pass
