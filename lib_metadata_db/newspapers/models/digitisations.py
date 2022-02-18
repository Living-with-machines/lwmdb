from django.db import models

from .newspapers_model import NewspapersModel


class Digitisation(NewspapersModel):
    xml_flavour = models.CharField(max_length=255, default="")
    software = models.CharField(max_length=30, default="")
    mets_namespace = models.CharField(max_length=255, default="")
    alto_namespace = models.CharField(max_length=255, default="")

    class Meta:
        app_label = "newspapers"
        db_table = "digitisations"

    def __str__(self):
        return f"{self.mets_namespace}, {self.alto_namespace}"
