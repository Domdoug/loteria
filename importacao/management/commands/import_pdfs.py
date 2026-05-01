"""Management command: importa PDFs da pasta configurada (settings.PDFS_DIR)."""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from importacao.services.importer import import_folder


class Command(BaseCommand):
    help = "Importa PDFs novos da pasta de entrada para o banco de dados."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=None,
            help="Pasta com os PDFs (default: settings.PDFS_DIR).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Apenas relata o que seria feito, sem alterar arquivos nem banco.",
        )

    def handle(self, *args, **options):
        folder = Path(options["path"]) if options["path"] else Path(settings.PDFS_DIR)
        if not folder.exists():
            self.stderr.write(self.style.ERROR(f"Pasta não encontrada: {folder}"))
            return

        self.stdout.write(f"Importando de: {folder}")
        summary = import_folder(folder, dry_run=options["dry_run"])

        self.stdout.write(self.style.SUCCESS("Resumo da importação:"))
        for campo in ("descobertos", "renomeados", "duplicados", "importados", "falhas", "ambiguos"):
            self.stdout.write(f"  {campo}: {getattr(summary, campo)}")
