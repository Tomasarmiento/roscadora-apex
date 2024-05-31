from django.urls import path, re_path
from . import views

urlpatterns = [
    # path('', views.ParameterListView.as_view(), name="parameters-list"),
    # path('update', views.update_parameters, name="parameters-update")
    path('', views.ParameterView.as_view(), name="parameters")
]