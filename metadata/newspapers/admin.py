from django.contrib import admin

from .models import DataProvider, Digitisation, Ingest, Newspaper, Issue, Item

# Register your models here.
admin.site.register(DataProvider)
admin.site.register(Digitisation)
admin.site.register(Ingest)
admin.site.register(Newspaper)
admin.site.register(Issue)
admin.site.register(Item)
