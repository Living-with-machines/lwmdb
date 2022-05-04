from django.db import models

from .press_directories_model import PressDirectoriesModel
from lib_metadata_db.gazetteer.models.place_of_publication import PlaceOfPublication


class Mitchells(PressDirectoriesModel):
    title = models.CharField(max_length=255, default=None, null=True)
    political_leaning_1 = models.CharField(max_length=255, default=None, null=True)
    political_leaning_2 = models.CharField(max_length=255, default=None, null=True)
    political_leaning_raw = models.JSONField(null=True)
    price_1 = models.CharField(max_length=255, default=None, null=True)
    price_2 = models.CharField(max_length=255, default=None, null=True)
    price_raw = models.JSONField(null=True)
    year = models.DateField(blank=True, null=True)
    date_established_raw = models.JSONField(null=True)
    day_of_publication_raw = models.CharField(max_length=255, default=None, null=True)
    place_of_circulation_raw = models.CharField(max_length=2550, default=None, null=True)
    publication_district_raw = models.CharField(max_length=255, default=None, null=True)
    publication_county_raw = models.CharField(max_length=255, default=None, null=True)
    organisations = models.CharField(max_length=255, default=None, null=True)
    persons = models.CharField(max_length=510, default=None, null=True)
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
