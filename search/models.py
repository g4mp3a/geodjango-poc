from django.contrib.gis.db import models
from .constants import US_STATES

class Business(models.Model):
    name = models.CharField()
    city = models.CharField(max_length=128, default="")
    state = models.CharField(max_length=2, choices=US_STATES, default="")
    location = models.PointField()

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.city}, {self.state})"
