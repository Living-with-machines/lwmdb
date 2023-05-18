from django.contrib import admin

from .models import Entry, Issue, PoliticalLeaning, Price

admin.site.register(Issue)
admin.site.register(PoliticalLeaning)
admin.site.register(Entry)
admin.site.register(Price)
