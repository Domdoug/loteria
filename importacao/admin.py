from django.contrib import admin

from .models import ArquivoImportado, LogImportacao


@admin.register(ArquivoImportado)
class ArquivoImportadoAdmin(admin.ModelAdmin):
    list_display = (
        "nome_arquivo_atual",
        "status_importacao",
        "quantidade_paginas",
        "data_detectada",
        "data_importacao",
    )
    list_filter = ("status_importacao",)
    search_fields = ("nome_arquivo_atual", "nome_arquivo_original", "hash_arquivo")
    readonly_fields = ("hash_arquivo", "data_detectada", "data_importacao", "texto_extraido")


@admin.register(LogImportacao)
class LogImportacaoAdmin(admin.ModelAdmin):
    list_display = ("data_hora", "nivel", "etapa", "arquivo_relacionado")
    list_filter = ("nivel", "etapa")
    search_fields = ("mensagem", "etapa")
