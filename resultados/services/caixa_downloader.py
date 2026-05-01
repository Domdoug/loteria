"""Download do ZIP de resultados da Mega-Sena no portal da Caixa.

A página oficial https://loterias.caixa.gov.br/Paginas/Mega-Sena.aspx expõe um
botão "Resultados da Mega-Sena por ordem crescente" que aponta para um ZIP
com o histórico completo. A URL pode mudar; por isso ela é configurável via a
variável de ambiente MEGASENA_RESULTS_URL.
"""

from __future__ import annotations

import os
from pathlib import Path

import requests

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def url_padrao() -> str | None:
    return os.getenv("MEGASENA_RESULTS_URL") or None


def baixar_zip(destino: Path, url: str | None = None, *, timeout: int = 30) -> Path:
    """Baixa o ZIP da Caixa para `destino`. Devolve o caminho final."""
    url_efetiva = url or url_padrao()
    if not url_efetiva:
        raise RuntimeError(
            "URL do ZIP da Mega-Sena não configurada. Defina MEGASENA_RESULTS_URL "
            "no .env ou passe --url no command."
        )
    destino.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    with requests.get(url_efetiva, headers=headers, stream=True, timeout=timeout) as resp:
        resp.raise_for_status()
        with destino.open("wb") as fh:
            for chunk in resp.iter_content(chunk_size=64 * 1024):
                if chunk:
                    fh.write(chunk)
    return destino
