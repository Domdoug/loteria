"""Script auxiliar (não-Django) para amostrar texto de alguns PDFs.

Uso:
    python scripts/sample_pdfs.py 01062024.pdf 03012026.pdf 05112024_pt1.pdf
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from importacao.services.normalizer import normalize  # noqa: E402
from importacao.services.pdf_reader import extract_text  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        print("uso: python scripts/sample_pdfs.py arq1.pdf arq2.pdf ...")
        sys.exit(2)
    base = Path(__file__).resolve().parent.parent / "pdfs"
    for nome in sys.argv[1:]:
        path = base / nome
        if not path.exists():
            print(f"--- {nome}: NÃO ENCONTRADO em {base}")
            continue
        result = extract_text(path)
        texto = normalize(result.texto)
        print(f"\n===== {nome} ({result.paginas} pág, extrator={result.extrator}) =====")
        if result.aviso:
            print(f"[aviso] {result.aviso}")
        print(texto[:4000])
        if len(texto) > 4000:
            print(f"... [+{len(texto) - 4000} chars truncados]")


if __name__ == "__main__":
    main()
