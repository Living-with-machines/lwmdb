from django.core.management import BaseCommand

from lib_metadata_db.gazetteer.models.place_of_publication import PlaceOfPublication
from lib_metadata_db.gazetteer.models.admin_county import AdminCounty
from lib_metadata_db.gazetteer.models.historic_county import HistoricCounty
from lib_metadata_db.gazetteer.models.country import Country


class Command(BaseCommand):
    def handle(self, *args, **options):
        PlaceOfPublication.objects.all().delete()
        AdminCounty.objects.all().delete()
        HistoricCounty.objects.all().delete()
        Country.objects.all().delete()
