from django.db import models

from .newspapers_model import NewspapersModel
from lib_metadata_db.press_directories.models.mitchells import Mitchells


class MitchellsPublication(NewspapersModel):
    year = models.DateField(null=True, blank=True)
    mitchells = models.ForeignKey(
        Mitchells, on_delete=models.SET_NULL, verbose_name="mitchells", null=True
    )

    class Meta:
        app_label = "newspapers"
        db_table = "mitchells_publications"

    def __str__(self):
        return str(self.year)
