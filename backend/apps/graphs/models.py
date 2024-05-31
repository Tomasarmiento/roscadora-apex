from django.db import models

# Create your models here.
class Graph(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    graph_data = models.JSONField(default=dict)

    def __str__(self) -> str:
        return 'Grafico ' + str(self.id)