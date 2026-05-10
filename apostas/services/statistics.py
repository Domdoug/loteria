"""Estatísticas de números jogados e totais financeiros."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal

from django.db.models import Count, QuerySet, Sum

from apostas.models import Aposta, Comprovante, NumeroApostado


def total_gasto(qs: QuerySet[Comprovante]) -> Decimal:
    valor = qs.aggregate(s=Sum("valor_total_aposta"))["s"]
    return valor or Decimal("0")


def total_por_tipo_jogo(qs: QuerySet[Comprovante]) -> list[dict]:
    return list(
        qs.values("tipo_jogo__nome", "tipo_jogo__slug")
        .annotate(total=Sum("valor_total_aposta"), comprovantes=Count("id"))
        .order_by("-total")
    )


def acertos_megasena(qs: QuerySet[Comprovante]) -> dict[int, int]:
    """Retorna {comprovante_id: melhor_acerto} para Mega-Sena com dezenas gravadas.

    Só inclui comprovantes com pelo menos 4 acertos em alguma aposta.
    """
    from resultados.models import ResultadoMegaSena

    mega_ids = list(
        qs.filter(tipo_jogo__nome="Mega-Sena").values_list("id", flat=True)
    )
    if not mega_ids:
        return {}

    apostas = list(
        Aposta.objects.filter(comprovante_id__in=mega_ids)
        .annotate(num_dezenas=Count("numeros"))
        .filter(num_dezenas__gt=0)
        .values("id", "comprovante_id", "concurso")
    )
    if not apostas:
        return {}

    concursos_validos = {
        a["concurso"] for a in apostas if a["concurso"].isdigit()
    }
    resultados = {
        str(r.concurso): set(r.dezenas())
        for r in ResultadoMegaSena.objects.filter(
            concurso__in=[int(c) for c in concursos_validos]
        )
    }
    if not resultados:
        return {}

    aposta_ids = [a["id"] for a in apostas]
    numeros_por_aposta: dict[int, set[int]] = {}
    for n in NumeroApostado.objects.filter(aposta_id__in=aposta_ids).values("aposta_id", "numero"):
        numeros_por_aposta.setdefault(n["aposta_id"], set()).add(n["numero"])

    melhores: dict[int, int] = {}
    for a in apostas:
        sorteadas = resultados.get(a["concurso"])
        apostadas = numeros_por_aposta.get(a["id"])
        if not sorteadas or not apostadas:
            continue
        acertos = len(apostadas & sorteadas)
        if acertos >= 4:
            comp_id = a["comprovante_id"]
            melhores[comp_id] = max(melhores.get(comp_id, 0), acertos)

    return melhores


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
