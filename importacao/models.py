from django.db import models


class ArquivoImportado(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        EM_PROCESSAMENTO = "em_processamento", "Em processamento"
        SUCESSO = "sucesso", "Sucesso"
        FALHA = "falha", "Falha"
        IGNORADO = "ignorado", "Ignorado"

    nome_arquivo_original = models.CharField(max_length=255)
    nome_arquivo_atual = models.CharField(max_length=255)
    caminho_arquivo = models.CharField(max_length=500)
    hash_arquivo = models.CharField(max_length=64, unique=True)
    data_detectada = models.DateTimeField(auto_now_add=True)
    data_importacao = models.DateTimeField(null=True, blank=True)
    status_importacao = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDENTE
    )
    mensagem_erro = models.TextField(blank=True, default="")
    texto_extraido = models.TextField(blank=True, default="")
    quantidade_paginas = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-data_detectada"]
        verbose_name = "Arquivo importado"
        verbose_name_plural = "Arquivos importados"

    def __str__(self) -> str:
        return f"{self.nome_arquivo_atual} ({self.status_importacao})"


class LogImportacao(models.Model):
    class Nivel(models.TextChoices):
        DEBUG = "debug", "Debug"
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"

    arquivo_relacionado = models.ForeignKey(
        ArquivoImportado,
        on_delete=models.CASCADE,
        related_name="logs",
        null=True,
        blank=True,
    )
    etapa = models.CharField(max_length=80)
    nivel = models.CharField(max_length=10, choices=Nivel.choices, default=Nivel.INFO)
    mensagem = models.TextField()
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data_hora"]
        verbose_name = "Log de importação"
        verbose_name_plural = "Logs de importação"

    def __str__(self) -> str:
        return f"[{self.nivel}] {self.etapa}: {self.mensagem[:60]}"
