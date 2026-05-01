"""Filtragem da listagem de comprovantes/apostas."""

from __future__ import annotations

from datetime import date

from django.db.models import QuerySet

from apostas.models import Comprovante


def filtrar_comprovantes(
    *,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    tipo_jogo_slug: str | None = None,
) -> QuerySet[Comprovante]:
    qs = Comprovante.objects.select_related("tipo_jogo", "arquivo_importado").all()
    if data_inicio:
        qs = qs.filter(data_jogo__gte=data_inicio)
    if data_fim:
        qs = qs.filter(data_jogo__lte=data_fim)
    if tipo_jogo_slug:
        qs = qs.filter(tipo_jogo__slug=tipo_jogo_slug)
    return qs
