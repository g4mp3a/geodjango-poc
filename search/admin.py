from django.contrib.gis import admin
from search.models import Business


@admin.register(Business)
class BusinessAdmin(admin.GISModelAdmin):
    list_display = ("name", "city", "state", "location")