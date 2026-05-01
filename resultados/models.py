from django.db import models


class ResultadoMegaSena(models.Model):
    concurso = models.PositiveIntegerField(unique=True)
    data_apuracao = models.DateField()
    dezena_1 = models.PositiveSmallIntegerField()
    dezena_2 = models.PositiveSmallIntegerField()
    dezena_3 = models.PositiveSmallIntegerField()
    dezena_4 = models.PositiveSmallIntegerField()
    dezena_5 = models.PositiveSmallIntegerField()
    dezena_6 = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["-concurso"]
        verbose_name = "Resultado Mega-Sena"
        verbose_name_plural = "Resultados Mega-Sena"

    def dezenas(self) -> list[int]:
        return [
            self.dezena_1,
            self.dezena_2,
            self.dezena_3,
            self.dezena_4,
            self.dezena_5,
            self.dezena_6,
        ]

    def __str__(self) -> str:
        return f"Concurso {self.concurso} ({self.data_apuracao.isoformat()})"
