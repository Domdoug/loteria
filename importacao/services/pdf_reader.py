"""Extração de texto bruto de PDFs.

Estratégia:
- pdfplumber como leitor principal (melhor para layouts em colunas)
- pypdf como fallback caso o primeiro falhe
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pdfplumber
from pypdf import PdfReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PdfTextResult:
    texto: str
    paginas: int
    extrator: str  # "pdfplumber" | "pypdf"
    aviso: str = ""


def extract_text(path: Path) -> PdfTextResult:
    try:
        with pdfplumber.open(str(path)) as pdf:
            paginas = len(pdf.pages)
            partes: list[str] = []
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                partes.append(page_text)
            texto = "\n\n".join(partes).strip()
        if texto:
            return PdfTextResult(texto=texto, paginas=paginas, extrator="pdfplumber")
        aviso = "pdfplumber retornou texto vazio; usando fallback pypdf"
    except Exception as exc:
        aviso = f"pdfplumber falhou ({exc.__class__.__name__}: {exc}); usando fallback pypdf"
        logger.warning("Falha pdfplumber em %s: %s", path.name, exc)

    reader = PdfReader(str(path))
    paginas = len(reader.pages)
    partes = [(p.extract_text() or "") for p in reader.pages]
    texto = "\n\n".join(partes).strip()
    return PdfTextResult(texto=texto, paginas=paginas, extrator="pypdf", aviso=aviso)
