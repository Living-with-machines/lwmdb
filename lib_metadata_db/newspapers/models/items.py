from django.db import models

from .newspapers_model import NewspapersModel
from .issues import Issue
from .data_providers import DataProvider
from .digitisations import Digitisation
from .ingest import Ingest


class Item(NewspapersModel):
    item_code = models.CharField(max_length=30, default="")
    title = models.CharField(max_length=255, default="")
    item_type = models.CharField(max_length=10, default="")
    word_count = models.IntegerField(null=True, db_index=True)
    ocr_quality_mean = models.FloatField(null=True)
    ocr_quality_sd = models.FloatField(null=True)
    input_filename = models.CharField(max_length=255, default="")
    issue = models.ForeignKey(
        Issue, on_delete=models.SET_NULL, verbose_name="issue", null=True
    )
    data_provider = models.ForeignKey(
        DataProvider, on_delete=models.SET_NULL, verbose_name="data_provider", null=True
    )
    digitisation = models.ForeignKey(
        Digitisation, on_delete=models.SET_NULL, verbose_name="digitisation", null=True
    )
    ingest = models.ForeignKey(
        Ingest, on_delete=models.SET_NULL, verbose_name="ingest", null=True
    )

    class Meta:
        app_label = "newspapers"
        db_table = "items"

    def __str__(self):
        return str(self.item_code)
