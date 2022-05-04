from django.db import models

from .newspapers_model import NewspapersModel
from .issues import Issue
from .data_providers import DataProvider
from .digitisations import Digitisation
from .ingest import Ingest


class Item(NewspapersModel):
    item_code = models.CharField(max_length=600, default=None)
    title = models.TextField(default=None)
    item_type = models.CharField(max_length=600, default=None)
    word_count = models.IntegerField(null=True, db_index=True)
    ocr_quality_mean = models.FloatField(null=True, blank=True)
    ocr_quality_sd = models.FloatField(null=True, blank=True)
    input_filename = models.CharField(max_length=255, default=None)
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
