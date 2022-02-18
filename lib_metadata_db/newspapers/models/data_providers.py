from django.db import models

from .newspapers_model import NewspapersModel


class DataProvider(NewspapersModel):
    name = models.CharField(max_length=30, default="")
    collection = models.CharField(max_length=30, default="")
    source_note = models.CharField(max_length=255, default="")

    class Meta:
        app_label = "newspapers"
        db_table = "data_providers"

    def __str__(self):
        return str(self.name)
