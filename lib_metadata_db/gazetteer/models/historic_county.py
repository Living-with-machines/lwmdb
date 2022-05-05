from django.db import models

from .gazetteer_model import GazetteerModel


class HistoricCounty(GazetteerModel):
    hcounty_label = models.CharField(max_length=255, default=None)
    hcounty_wikidata_id = models.CharField(max_length=30, default=None)

    class Meta:
        app_label = "gazetteer"
        db_table = "historic_county"

    def __str__(self):
        return str(self.hcounty_label)
