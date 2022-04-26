from django.db import models

from .gazetteer_model import GazetteerModel


class Country(GazetteerModel):
    country_label = models.CharField(max_length=255, default="")
    country_wikidata_id = models.CharField(max_length=30, default="")

    class Meta:
        app_label = "gazetteer"
        db_table = "country"

    def __str__(self):
        return str(self.country_label)
