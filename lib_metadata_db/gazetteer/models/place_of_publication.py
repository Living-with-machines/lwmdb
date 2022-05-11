from django.db import models

from .gazetteer_model import GazetteerModel
from .historic_county import HistoricCounty
from .admin_county import AdminCounty
from .country import Country


class PlaceOfPublication(GazetteerModel):
    place_wikidata_id = models.CharField(max_length=30, default=None)
    place_label = models.CharField(max_length=255, default=None)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    geonames_ids = models.CharField(max_length=255, default="")
    historic_county = models.ForeignKey(
        HistoricCounty,
        on_delete=models.SET_NULL,
        verbose_name="historic_county",
        null=True,
    )
    admin_county = models.ForeignKey(
        AdminCounty,
        on_delete=models.SET_NULL,
        verbose_name="admin_county",
        null=True,
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        verbose_name="county",
        null=True,
    )

    class Meta:
        app_label = "gazetteer"
        db_table = "place_of_publication"

    def __str__(self):
        return str(self.place_label)
