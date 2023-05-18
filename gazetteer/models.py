from django.contrib.gis.db import models


class GazetteerModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AdminCounty(GazetteerModel):
    label = models.CharField(max_length=255, default=None)
    wikidata_id = models.CharField(max_length=30, default=None)
    geom = models.GeometryCollectionField(null=True)

    def __str__(self):
        return str(self.label)

    class Meta:
        unique_together = ("wikidata_id", "label")
        verbose_name_plural = "admin counties"


class Country(GazetteerModel):
    label = models.CharField(max_length=255, default=None)
    wikidata_id = models.CharField(max_length=30, default=None)
    geom = models.GeometryCollectionField(null=True)

    def __str__(self):
        return str(self.label)

    class Meta:
        unique_together = ("wikidata_id", "label")
        verbose_name_plural = "counties"


class HistoricCounty(GazetteerModel):
    label = models.CharField(max_length=255, default=None)
    wikidata_id = models.CharField(max_length=30, default=None)
    geom = models.GeometryCollectionField(null=True)

    def __str__(self):
        return str(self.label)

    class Meta:
        unique_together = ("wikidata_id", "label")
        verbose_name_plural = "historic counties"


class PlaceOfPublicationManager(models.Manager):
    def get_by_natural_key(self, wikidata_id, label):
        return self.get(wikidata_id=wikidata_id, label=label)


class Place(GazetteerModel):
    wikidata_id = models.CharField(max_length=30, default=None)
    label = models.CharField(max_length=255, default=None)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    geonames_ids = models.CharField(max_length=255, default=None, null=True)
    geom = models.GeometryCollectionField(null=True)

    historic_county = models.ForeignKey(
        HistoricCounty,
        on_delete=models.SET_NULL,
        verbose_name="historic_county",
        null=True,
        related_name="places",
        related_query_name="place",
    )
    admin_county = models.ForeignKey(
        AdminCounty,
        on_delete=models.SET_NULL,
        verbose_name="admin_county",
        null=True,
        related_name="places",
        related_query_name="place",
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        verbose_name="country",
        null=True,
        related_name="places",
        related_query_name="place",
    )

    objects = PlaceOfPublicationManager()

    class Meta:
        unique_together = ("wikidata_id", "label")

    def __str__(self):
        return str(self.label)
