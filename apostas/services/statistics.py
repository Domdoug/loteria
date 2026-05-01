"""Estatísticas de números jogados e totais financeiros."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal

from django.db.models import Count, QuerySet, Sum

from apostas.models import Comprovante, NumeroApostado


def total_gasto(qs: QuerySet[Comprovante]) -> Decimal:
    valor = qs.aggregate(s=Sum("valor_total_aposta"))["s"]
    return valor or Decimal("0")


def total_por_tipo_jogo(qs: QuerySet[Comprovante]) -> list[dict]:
    return list(
        qs.values("tipo_jogo__nome", "tipo_jogo__slug")
        .annotate(total=Sum("valor_total_aposta"), comprovantes=Count("id"))
        .order_by("-total")
    )


def numeros_mais_jogados(qs: QuerySet[Comprovante], limite: int = 15) -> list[tuple[int, int]]:
    """Top números apostados nos comprovantes filtrados.

    Hoje os PDFs não trazem os números no texto, então essa estatística retorna
    listagem vazia até a fase de OCR. A função fica preparada para quando os
    `NumeroApostado` começarem a ser populados.
    """
    counter: Counter[int] = Counter()
    numeros = NumeroApostado.objects.filter(aposta__comprovante__in=qs).values_list("numero", flat=True)
    for n in numeros:
        counter[n] += 1
    return counter.most_common(limite)
