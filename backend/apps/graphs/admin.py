from django.contrib import admin
from .models import Graph

# Register your models here.
class GraphAdmin(admin.ModelAdmin):
    fields = ('date', 'graph_data')
    list_filter = ('date',)
    readonly_fields = ('date',)

admin.site.register(Graph, GraphAdmin)