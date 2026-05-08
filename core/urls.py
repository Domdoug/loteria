from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apostas.urls")),
    path("resultados/", include("resultados.urls")),
]
