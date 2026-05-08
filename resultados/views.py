from __future__ import annotations

import tempfile
from pathlib import Path

from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from resultados.services.megasena_importer import importar_de_arquivo_xlsx

_MAX_SIZE = 10 * 1024 * 1024  # 10 MB


@require_POST
@csrf_protect
def atualizar_megasena(request):
    arquivo = request.FILES.get("xlsx")

    if not arquivo:
        messages.error(request, "Nenhum arquivo enviado.")
        return redirect("apostas:listagem")

    if arquivo.size > _MAX_SIZE:
        messages.error(request, f"Arquivo muito grande ({arquivo.size // 1024 // 1024} MB). Máximo: 10 MB.")
        return redirect("apostas:listagem")

    if not arquivo.name.lower().endswith(".xlsx"):
        messages.error(request, "Somente arquivos .xlsx são aceitos.")
        return redirect("apostas:listagem")

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        for chunk in arquivo.chunks():
            tmp.write(chunk)
        tmp_path = Path(tmp.name)

    try:
        resultado = importar_de_arquivo_xlsx(tmp_path)
    except Exception as exc:
        messages.error(request, f"Erro ao importar: {exc}")
        return redirect("apostas:listagem")
    finally:
        tmp_path.unlink(missing_ok=True)

    messages.success(
        request,
        f"Importação concluída: {resultado['criados']} concurso(s) novo(s), "
        f"{resultado['atualizados']} atualizado(s).",
    )
    return redirect("apostas:listagem")
