from django.urls import path

from . import views

app_name = "importacao"

urlpatterns = [
    path("importar-pdfs/", views.importar_pdfs_view, name="importar_pdfs"),
]
