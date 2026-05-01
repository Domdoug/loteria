"""Cálculo de hash SHA-256 dos arquivos para detecção de duplicidade."""

import hashlib
from pathlib import Path

_CHUNK = 1024 * 1024


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(_CHUNK)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
