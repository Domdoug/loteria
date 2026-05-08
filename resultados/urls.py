from django.urls import path

from . import views

app_name = "resultados"

urlpatterns = [
    path("atualizar-megasena/", views.atualizar_megasena, name="atualizar_megasena"),
]
