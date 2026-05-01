from django.urls import path

from . import views

app_name = "apostas"

urlpatterns = [
    path("", views.listagem_comprovantes, name="listagem"),
]
