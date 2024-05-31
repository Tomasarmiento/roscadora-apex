from django.db import models

# Create your models here.

class Parameter(models.Model):
    name = models.CharField(max_length=50, blank=False)
    description = models.CharField(max_length=255)
    unit = models.CharField(max_length=20)
    value = models.DecimalField(max_digits=10, decimal_places=3, blank=False)
    part_model = models.IntegerField(default=1, blank=False)

    def __str__(self):
        return self.name