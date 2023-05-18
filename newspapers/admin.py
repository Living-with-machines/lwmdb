from django.contrib import admin

from .models import DataProvider, Digitisation, Ingest, Issue, Item, Newspaper


class IssueAdmin(admin.TabularInline):
    model = Issue


@admin.register(Newspaper)
class NewspaperAdmin(admin.ModelAdmin):
    inlines = [IssueAdmin]
    search_fields = ["title"]
    list_filter = ["location"]


admin.site.register(DataProvider)
admin.site.register(Digitisation)
admin.site.register(Ingest)
admin.site.register(Item)
