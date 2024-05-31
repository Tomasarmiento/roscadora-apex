from django.contrib import admin
from .models import ChannelInfo

# Register your models here.
class ChannelInfoAdmin(admin.ModelAdmin):
    fields = ('source', 'name')

admin.site.register(ChannelInfo, ChannelInfoAdmin)