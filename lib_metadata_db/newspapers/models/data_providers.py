from django.db import models

from .newspapers_model import NewspapersModel


class DataProvider(NewspapersModel):
    name = models.CharField(max_length=600, default=None)
    collection = models.CharField(max_length=600, default=None)
    source_note = models.CharField(max_length=255, default=None)

    class Meta:
        app_label = "newspapers"
        db_table = "data_providers"

    def __str__(self):
        return str(self.name)
