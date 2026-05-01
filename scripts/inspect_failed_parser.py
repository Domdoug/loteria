import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django  # noqa: E402

django.setup()

from importacao.models import ArquivoImportado  # noqa: E402

out = Path(__file__).resolve().parent.parent / "_failed_parser_dump.txt"
with out.open("w", encoding="utf-8") as fh:
    for arq in ArquivoImportado.objects.filter(mensagem_erro__startswith="Nenhum comprovante"):
        fh.write(f"===== {arq.nome_arquivo_atual} (páginas={arq.quantidade_paginas}) =====\n")
        fh.write(arq.texto_extraido[:3000])
        fh.write("\n\n")
print(f"escrito em {out}")
