"""Command: importa resultados oficiais da Mega-Sena.

Suporta três fontes (em ordem de precedência):
  1. --html <path>  : caminho para um arquivo HTML/HTM já extraído
  2. --zip  <path>  : caminho para um ZIP local; o arquivo HTML é encontrado dentro
  3. --download     : baixa o ZIP da Caixa via MEGASENA_RESULTS_URL e processa
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from resultados.services.caixa_downloader import baixar_zip
from resultados.services.megasena_importer import importar_de_arquivo_html
from resultados.services.zip_extractor import extrair_zip


class Command(BaseCommand):
    help = "Importa resultados oficiais da Mega-Sena a partir de HTML, ZIP local ou download."

    def add_arguments(self, parser):
        parser.add_argument("--html", default=None, help="Caminho de um HTML já extraído.")
        parser.add_argument("--zip", default=None, dest="zip_path", help="Caminho de um ZIP local.")
        parser.add_argument(
            "--download",
            action="store_true",
            help="Baixa o ZIP da Caixa (requer MEGASENA_RESULTS_URL no .env).",
        )
        parser.add_argument("--url", default=None, help="Sobrescreve a URL do ZIP.")

    def handle(self, *args, **options):
        html_path = self._resolver_html(options)
        try:
            resumo = importar_de_arquivo_html(html_path)
        finally:
            tmpdir = getattr(self, "_tmpdir", None)
            if tmpdir:
                shutil.rmtree(tmpdir, ignore_errors=True)

        self.stdout.write(self.style.SUCCESS("Resumo da importação Mega-Sena:"))
        for k, v in resumo.items():
            self.stdout.write(f"  {k}: {v}")

    def _resolver_html(self, options) -> Path:
        if options["html"]:
            html_path = Path(options["html"])
            if not html_path.exists():
                raise CommandError(f"HTML não encontrado: {html_path}")
            return html_path

        zip_path: Path | None
        if options["zip_path"]:
            zip_path = Path(options["zip_path"])
            if not zip_path.exists():
                raise CommandError(f"ZIP não encontrado: {zip_path}")
        elif options["download"]:
            tmpdir = Path(tempfile.mkdtemp(prefix="megasena_"))
            self._tmpdir = str(tmpdir)
            zip_path = tmpdir / "megasena.zip"
            try:
                baixar_zip(zip_path, url=options["url"])
            except Exception as exc:
                raise CommandError(f"Falha no download: {exc}") from exc
        else:
            raise CommandError("Use --html, --zip ou --download.")

        tmpdir = Path(tempfile.mkdtemp(prefix="megasena_extract_"))
        self._tmpdir = str(getattr(self, "_tmpdir", tmpdir.parent)) if False else str(tmpdir)
        extraidos = extrair_zip(zip_path, tmpdir)
        htmls = [p for p in extraidos if p.suffix.lower() in {".htm", ".html"}]
        if not htmls:
            raise CommandError(f"Nenhum HTML/HTM encontrado dentro de {zip_path}.")
        return htmls[0]
