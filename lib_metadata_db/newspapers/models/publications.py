from django.db import models

from .newspapers_model import NewspapersModel


class Publication(NewspapersModel):
    publication_code = models.CharField(max_length=30, default="")
    title = models.CharField(max_length=255, default="")
    location = models.CharField(max_length=255, default="")

    class Meta:
        app_label = "newspapers"
        db_table = "publications"

    def __str__(self):
        return str(self.publication_code)
