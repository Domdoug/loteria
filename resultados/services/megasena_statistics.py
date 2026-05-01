"""Estatísticas das dezenas mais sorteadas na Mega-Sena."""

from __future__ import annotations

from collections import Counter

from resultados.models import ResultadoMegaSena


def numeros_mais_sorteados(limite: int = 15) -> list[tuple[int, int]]:
    counter: Counter[int] = Counter()
    for r in ResultadoMegaSena.objects.all().only(
        "dezena_1", "dezena_2", "dezena_3", "dezena_4", "dezena_5", "dezena_6"
    ):
        for n in r.dezenas():
            counter[n] += 1
    return counter.most_common(limite)
