from django.db import models

# Create your models here.
class ChannelInfo(models.Model):
    source = models.CharField(blank=True, max_length=10)
    name = models.CharField(max_length=255, blank=True)
    log = models.SmallIntegerField(default=0)