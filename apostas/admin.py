from django.contrib import admin

from .models import Aposta, Comprovante, NumeroApostado, TipoJogo


@admin.register(TipoJogo)
class TipoJogoAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "slug")
    prepopulated_fields = {"slug": ("nome",)}


class ApostaInline(admin.TabularInline):
    model = Aposta
    extra = 0
    fields = ("sequencia", "concurso", "descricao", "valor_aposta")


@admin.register(Comprovante)
class ComprovanteAdmin(admin.ModelAdmin):
    list_display = ("data_jogo", "tipo_jogo", "valor_total_aposta", "arquivo_importado")
    list_filter = ("tipo_jogo",)
    search_fields = ("codigo_autenticacao", "arquivo_importado__nome_arquivo_atual")
    inlines = [ApostaInline]


@admin.register(Aposta)
class ApostaAdmin(admin.ModelAdmin):
    list_display = ("comprovante", "sequencia", "concurso", "valor_aposta")
    search_fields = ("concurso", "descricao")


@admin.register(NumeroApostado)
class NumeroApostadoAdmin(admin.ModelAdmin):
    list_display = ("aposta", "ordem", "numero")
    list_filter = ("numero",)
