from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from importacao.services.importer import import_folder


@require_POST
@csrf_protect
def importar_pdfs_view(request):
    summary = import_folder(settings.PDFS_DIR)

    if summary.importados > 0:
        messages.success(
            request,
            f"{summary.importados} comprovante(s) novo(s) importado(s)."
            + (f" {summary.falhas} falha(s)." if summary.falhas else ""),
        )
    elif summary.falhas > 0:
        messages.error(request, f"Nenhum comprovante novo. {summary.falhas} falha(s).")
    else:
        messages.info(request, "Nenhum arquivo novo encontrado.")

    return redirect("apostas:listagem")
