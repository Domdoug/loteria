from django.contrib import admin

from .models import ResultadoMegaSena


@admin.register(ResultadoMegaSena)
class ResultadoMegaSenaAdmin(admin.ModelAdmin):
    list_display = ("concurso", "data_apuracao", "dezena_1", "dezena_2", "dezena_3", "dezena_4", "dezena_5", "dezena_6")
    search_fields = ("concurso",)
    list_filter = ("data_apuracao",)
