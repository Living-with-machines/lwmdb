from django.db import models

from newspapers.models import Newspaper
from gazetteer.models import Place


class PressDirectoriesModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Issue(PressDirectoriesModel):
    year = models.PositiveSmallIntegerField(null=True, blank=True, default=None)

    def __str__(self):
        return str(self.year)


class PoliticalLeaning(PressDirectoriesModel):
    label = models.CharField(max_length=255, default=None, null=True)

    def __str__(self):
        return str(self.label)


class Price(PressDirectoriesModel):
    label = models.CharField(max_length=255, default=None, null=True)

    def __str__(self):
        return str(self.label)


class EntryPrices(models.Model):
    entry = models.ForeignKey("mitchells.Entry", on_delete=models.CASCADE)
    price = models.ForeignKey(Price, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=1, blank=True, null=True)

    class Meta:
        ordering = ("order",)


class EntryPoliticalLeanings(models.Model):
    entry = models.ForeignKey("mitchells.Entry", on_delete=models.CASCADE)
    political_leaning = models.ForeignKey(PoliticalLeaning, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=1, blank=True, null=True)

    class Meta:
        ordering = ("order",)


class Entry(PressDirectoriesModel):
    title = models.CharField(max_length=255, default=None, null=True)
    political_leaning_raw = models.JSONField(null=True)
    price_raw = models.JSONField(null=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True, default=None)
    date_established_raw = models.JSONField(null=True)
    day_of_publication_raw = models.CharField(max_length=255, default=None, null=True)
    place_of_circulation_raw = models.CharField(
        max_length=2550, default=None, null=True
    )
    publication_district_raw = models.CharField(max_length=255, default=None, null=True)
    publication_county_raw = models.CharField(max_length=255, default=None, null=True)
    organisations = models.CharField(max_length=255, default=None, null=True)
    persons = models.CharField(max_length=510, default=None, null=True)
    place_of_publication = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        verbose_name="place_of_publication",
        null=True,
        related_name="mitchells",
        related_query_name="mitchells",
    )
    issue = models.ForeignKey(
        Issue,
        on_delete=models.SET_NULL,
        related_name="entries",
        related_query_name="entry",
        null=True,
        default=None,
    )
    newspaper = models.ForeignKey(
        Newspaper,
        on_delete=models.SET_NULL,
        related_name="mitchells_entries",
        related_query_name="mitchells_entry",
        null=True,
        default=None,
    )
    political_leanings = models.ManyToManyField(
        PoliticalLeaning,
        related_name="entries",
        related_query_name="entry",
        through=EntryPoliticalLeanings,
    )
    prices = models.ManyToManyField(
        Price, related_name="entries", related_query_name="entry", through=EntryPrices
    )

    def __str__(self):
        return f"{self.title} ({self.year})"
