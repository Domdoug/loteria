from django.shortcuts import render

from resultados.services.megasena_statistics import numeros_mais_sorteados

from .forms import FiltroComprovanteForm
from .services.filters import filtrar_comprovantes
from .services.statistics import (
    numeros_mais_jogados,
    total_gasto,
    total_por_tipo_jogo,
)


def listagem_comprovantes(request):
    form = FiltroComprovanteForm(request.GET or None)
    data_inicio = data_fim = None
    tipo_slug = None
    if form.is_valid():
        data_inicio = form.cleaned_data.get("data_inicio")
        data_fim = form.cleaned_data.get("data_fim")
        tipo = form.cleaned_data.get("tipo_jogo")
        tipo_slug = tipo.slug if tipo else None

    qs = filtrar_comprovantes(
        data_inicio=data_inicio, data_fim=data_fim, tipo_jogo_slug=tipo_slug
    )
    qs = qs.prefetch_related("apostas").order_by("-data_jogo", "tipo_jogo__nome")

    contexto = {
        "form": form,
        "comprovantes": qs,
        "total_gasto": total_gasto(qs),
        "total_por_tipo_jogo": total_por_tipo_jogo(qs),
        "numeros_mais_jogados": numeros_mais_jogados(qs),
        "numeros_mais_sorteados_megasena": numeros_mais_sorteados(),
    }
    return render(request, "apostas/listagem.html", contexto)
