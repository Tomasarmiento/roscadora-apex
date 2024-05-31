from django.contrib import admin
from .models import RoutineInfo

# Register your models here.
class RoutineInfoAdmin(admin.ModelAdmin):
    fields = ['name', 'running']
    list_display = ['name', 'running']

admin.site.register(RoutineInfo, RoutineInfoAdmin)