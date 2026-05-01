"""Extração de ZIP da Caixa para uma pasta temporária."""

from __future__ import annotations

import zipfile
from pathlib import Path


def extrair_zip(zip_path: Path, destino: Path) -> list[Path]:
    """Extrai `zip_path` em `destino` e devolve a lista de arquivos extraídos."""
    destino.mkdir(parents=True, exist_ok=True)
    extraidos: list[Path] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for membro in zf.namelist():
            if membro.endswith("/"):
                continue
            zf.extract(membro, destino)
            extraidos.append(destino / membro)
    return extraidos
