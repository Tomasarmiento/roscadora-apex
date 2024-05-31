from django.contrib import admin
from.models import Parameter

class ParameterAdmin(admin.ModelAdmin):
    fields = ['name', 'value', 'unit', 'part_model']
    list_display = ['name', 'value', 'unit', 'part_model']
    list_filter = ('part_model',)

admin.site.register(Parameter, ParameterAdmin)

# Register your models here.
