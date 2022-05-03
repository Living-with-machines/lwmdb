from django.db import models

from .newspapers_model import NewspapersModel


class Digitisation(NewspapersModel):
    xml_flavour = models.CharField(max_length=255, default=None)
    software = models.CharField(max_length=600, default=None)
    mets_namespace = models.CharField(max_length=255, default=None)
    alto_namespace = models.CharField(max_length=255, default=None)

    class Meta:
        app_label = "newspapers"
        db_table = "digitisations"

    def __str__(self):
        return f"{self.mets_namespace}, {self.alto_namespace}"
