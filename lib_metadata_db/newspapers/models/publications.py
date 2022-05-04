from django.db import models

from .newspapers_model import NewspapersModel
from .mitchells_publications import MitchellsPublication


class Publication(NewspapersModel):
    publication_code = models.CharField(max_length=600, default=None)
    title = models.CharField(max_length=255, default=None)
    location = models.CharField(max_length=255, default=None)
    mitchells_publication = models.ForeignKey(
        MitchellsPublication, on_delete=models.SET_NULL, verbose_name="mitchells", null=True
    )

    class Meta:
        app_label = "newspapers"
        db_table = "publications"

    def __str__(self):
        return str(self.publication_code)
