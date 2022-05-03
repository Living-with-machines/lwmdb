from django.db import models

from .press_directories_model import PressDirectoriesModel
from lib_metadata_db.gazetteer.models.place_of_publication import PlaceOfPublication


class Mitchells(PressDirectoriesModel):
    title = models.CharField(max_length=255, default=None)
    political_leaning_1 = models.CharField(max_length=255, default=None)
    political_leaning_2 = models.CharField(max_length=255, default=None)
    political_leaning_raw = models.JSONField()
    price_1 = models.CharField(max_length=255, default=None)
    price_2 = models.CharField(max_length=255, default=None)
    price_raw = models.JSONField()
    year = models.DateField(null=True, blank=True)
    date_established_raw = models.JSONField()
    day_of_publication_raw = models.CharField(max_length=255, default=None)
    place_of_circulation_raw = models.CharField(max_length=2550, default=None)
    publication_district_raw = models.CharField(max_length=255, default=None)
    publication_county_raw = models.CharField(max_length=255, default=None)
    organisations = models.CharField(max_length=255, default=None)
    persons = models.CharField(max_length=510, default=None)
    place_of_publication = models.ForeignKey(
        PlaceOfPublication,
        on_delete=models.SET_NULL,
        verbose_name="place_of_publication",
        null=True,
    )
    
    class Meta:
        app_label = "press_directories"
        db_table = "mitchells"

    def __str__(self):
        return str(self.title)
