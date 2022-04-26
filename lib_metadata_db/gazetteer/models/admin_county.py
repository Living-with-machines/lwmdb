from django.db import models

from .gazetteer_model import GazetteerModel


class AdminCounty(GazetteerModel):
    admin_county_label = models.CharField(max_length=255, default="")
    admin_county_wikidata_id = models.CharField(max_length=30, default="")

    class Meta:
        app_label = "gazetteer"
        db_table = "admin_county"

    def __str__(self):
        return str(self.admin_county_label)
