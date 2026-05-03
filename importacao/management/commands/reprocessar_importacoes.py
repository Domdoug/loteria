"""Reprocessa arquivos importados com falha usando OCR."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from importacao.models import ArquivoImportado
from importacao.services.importer import reprocess_arquivo


class Command(BaseCommand):
    help = "Reprocessa arquivos com falha usando OCR (pdf2image + tesseract)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--arquivo",
            metavar="NOME",
            help="Reprocessar apenas o arquivo com esse nome.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Lista os arquivos que seriam reprocessados sem executar.",
        )

    def handle(self, *args, **options):
        qs = ArquivoImportado.objects.filter(status_importacao=ArquivoImportado.Status.FALHA)

        if options["arquivo"]:
            qs = qs.filter(nome_arquivo_atual=options["arquivo"])

        arquivos = list(qs.order_by("nome_arquivo_atual"))

        if not arquivos:
            self.stdout.write("Nenhum arquivo com falha encontrado.")
            return

        self.stdout.write(f"{len(arquivos)} arquivo(s) com falha encontrado(s).")

        if options["dry_run"]:
            for a in arquivos:
                self.stdout.write(f"  {a.nome_arquivo_atual} — {a.mensagem_erro}")
            return

        sucesso = 0
        falha = 0

        for arquivo in arquivos:
            # 20241217.pdf e similares: têm texto mas é só cabeçalho de browser;
            # o parser não encontra comprovantes → forçar OCR
            force_ocr = "Nenhum comprovante reconhecido" in (arquivo.mensagem_erro or "")

            self.stdout.write(
                f"Reprocessando {arquivo.nome_arquivo_atual}"
                + (" (OCR forçado)" if force_ocr else " (OCR automático)")
                + " ...",
                ending=" ",
            )
            self.stdout.flush()

            ok = reprocess_arquivo(arquivo, force_ocr=force_ocr)

            if ok:
                sucesso += 1
                self.stdout.write(self.style.SUCCESS("OK"))
            else:
                falha += 1
                arquivo.refresh_from_db(fields=["mensagem_erro"])
                self.stdout.write(self.style.ERROR(f"FALHA — {arquivo.mensagem_erro}"))

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(f"Concluído: {sucesso} sucesso(s), {falha} falha(s).")
        )
