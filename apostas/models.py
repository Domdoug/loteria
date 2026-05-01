from django.db import models
from django.utils.text import slugify


class TipoJogo(models.Model):
    nome = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Tipo de jogo"
        verbose_name_plural = "Tipos de jogo"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.nome


class Comprovante(models.Model):
    arquivo_importado = models.ForeignKey(
        "importacao.ArquivoImportado",
        on_delete=models.CASCADE,
        related_name="comprovantes",
    )
    tipo_jogo = models.ForeignKey(
        TipoJogo, on_delete=models.PROTECT, related_name="comprovantes"
    )
    data_jogo = models.DateField(null=True, blank=True)
    valor_total_aposta = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    codigo_autenticacao = models.CharField(max_length=120, blank=True, default="")
    observacoes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-data_jogo", "id"]
        verbose_name = "Comprovante"
        verbose_name_plural = "Comprovantes"

    def __str__(self) -> str:
        data = self.data_jogo.isoformat() if self.data_jogo else "sem data"
        return f"{self.tipo_jogo.nome} — {data}"


class Aposta(models.Model):
    comprovante = models.ForeignKey(
        Comprovante, on_delete=models.CASCADE, related_name="apostas"
    )
    sequencia = models.PositiveIntegerField(default=1)
    descricao = models.CharField(max_length=120, blank=True, default="")
    concurso = models.CharField(max_length=20, blank=True, default="")
    valor_aposta = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["comprovante_id", "sequencia"]
        verbose_name = "Aposta"
        verbose_name_plural = "Apostas"

    def __str__(self) -> str:
        return f"Aposta #{self.sequencia} ({self.comprovante})"


class NumeroApostado(models.Model):
    aposta = models.ForeignKey(
        Aposta, on_delete=models.CASCADE, related_name="numeros"
    )
    ordem = models.PositiveSmallIntegerField()
    numero = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["aposta_id", "ordem"]
        unique_together = [("aposta", "ordem")]
        verbose_name = "Número apostado"
        verbose_name_plural = "Números apostados"
        indexes = [models.Index(fields=["numero"])]

    def __str__(self) -> str:
        return f"{self.numero:02d}"
