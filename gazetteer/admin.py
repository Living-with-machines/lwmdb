from django.contrib import admin

from .models import AdminCounty, Country, HistoricCounty, Place

# Register your models here.
admin.site.register(AdminCounty)
admin.site.register(Country)
admin.site.register(HistoricCounty)
admin.site.register(Place)
