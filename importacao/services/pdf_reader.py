"""Extração de texto bruto de PDFs.

Estratégia:
- pdfplumber como leitor principal (melhor para layouts em colunas)
- pypdf como fallback caso o primeiro falhe
- OCR (pdf2image + tesseract) quando ambos retornam vazio, ou sob demanda

Para PDFs imagem: usa pytesseract.image_to_data com reordenação por linha
(y, x) para reconstruir a leitura da tabela de comprovantes corretamente.
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
    extrator: str  # "pdfplumber" | "pypdf" | "ocr"
    aviso: str = ""


def _row_sorted_text(img) -> str:
    """Converte imagem em texto reordenando palavras por (y, x) para leitura por linha."""
    import pytesseract

    data = pytesseract.image_to_data(img, lang="por", output_type=pytesseract.Output.DATAFRAME)
    data = data[(data.conf > 20) & (data.text.notna()) & (data.text.str.strip() != "")].copy()

    if data.empty:
        return ""

    data["cy"] = data["top"] + data["height"] / 2
    data = data.sort_values(["cy", "left"])

    threshold = int(data["height"].median() * 0.7)
    rows: list[str] = []
    cur: list[str] = []
    cur_y: float | None = None

    for _, w in data.iterrows():
        cy = float(w["cy"])
        if cur_y is None or abs(cy - cur_y) <= threshold:
            cur.append(str(w["text"]))
            if cur_y is None:
                cur_y = cy
        else:
            if cur:
                rows.append(" ".join(cur))
            cur, cur_y = [str(w["text"])], cy

    if cur:
        rows.append(" ".join(cur))

    return "\n".join(rows)


def _extract_ocr(path: Path, *, aviso: str = "", paginas: int = 0) -> PdfTextResult:
    """Extrai texto via OCR usando pdf2image + tesseract com row-sorting."""
    try:
        from pdf2image import convert_from_path
        import pytesseract  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "OCR indisponível: instale pdf2image e pytesseract"
        ) from exc

    from pdf2image import convert_from_path

    images = convert_from_path(str(path), dpi=200)
    paginas = paginas or len(images)
    partes: list[str] = []

    for img in images:
        try:
            page_text = _row_sorted_text(img)
        except Exception:
            # fallback para image_to_string se image_to_data falhar
            import pytesseract
            page_text = pytesseract.image_to_string(img, lang="por")
        partes.append(page_text)

    texto = "\n\n".join(partes).strip()
    return PdfTextResult(texto=texto, paginas=paginas, extrator="ocr", aviso=aviso)


def extract_text(path: Path, *, force_ocr: bool = False) -> PdfTextResult:
    """Extrai texto do PDF.

    Fluxo normal: pdfplumber → pypdf → OCR (se ambos retornarem vazio).
    force_ocr=True: pula pdfplumber/pypdf e vai direto ao OCR.
    """
    if force_ocr:
        return _extract_ocr(path, aviso="OCR forçado")

    aviso = ""
    paginas = 0

    # 1. pdfplumber
    try:
        with pdfplumber.open(str(path)) as pdf:
            paginas = len(pdf.pages)
            partes: list[str] = [page.extract_text() or "" for page in pdf.pages]
            texto = "\n\n".join(partes).strip()
        if texto:
            return PdfTextResult(texto=texto, paginas=paginas, extrator="pdfplumber")
        aviso = "pdfplumber retornou texto vazio; usando fallback pypdf"
    except Exception as exc:
        aviso = f"pdfplumber falhou ({exc.__class__.__name__}: {exc}); usando fallback pypdf"
        logger.warning("Falha pdfplumber em %s: %s", path.name, exc)

    # 2. pypdf
    reader = PdfReader(str(path))
    paginas = paginas or len(reader.pages)
    partes = [(p.extract_text() or "") for p in reader.pages]
    texto = "\n\n".join(partes).strip()
    if texto:
        return PdfTextResult(texto=texto, paginas=paginas, extrator="pypdf", aviso=aviso)

    # 3. OCR — ambos extratores retornaram vazio
    aviso_ocr = (aviso + "; " if aviso else "") + "ambos extratores retornaram vazio; usando OCR"
    return _extract_ocr(path, aviso=aviso_ocr, paginas=paginas)
