from django.db import models

# Create your models here.
class RoutineInfo(models.Model):
    name = models.CharField(blank=False, max_length=20)
    running = models.IntegerField(blank=False, default=0)