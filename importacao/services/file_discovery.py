"""Descoberta dos PDFs disponíveis na pasta de entrada."""

from collections.abc import Iterator
from pathlib import Path


def discover_pdfs(folder: Path) -> Iterator[Path]:
    """Itera sobre os PDFs da pasta indicada (sem recursão).

    A ordem é determinística (alfabética pelo nome do arquivo) para que a
    importação seja reproduzível.
    """
    if not folder.exists():
        return iter(())
    return iter(
        sorted(
            (p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"),
            key=lambda p: p.name.lower(),
        )
    )
