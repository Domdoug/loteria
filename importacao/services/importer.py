"""Orquestrador da importação: descoberta → renomeação → hash → texto → parse → persistência."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from django.db import transaction
from django.utils import timezone

from apostas.models import Aposta, Comprovante, NumeroApostado, TipoJogo
from importacao.models import ArquivoImportado, LogImportacao

from .file_discovery import discover_pdfs
from .file_rename import apply_rename, propose_rename
from .hash_service import file_sha256
from .normalizer import normalize
from .parser import parse_compra
from .pdf_reader import extract_text

logger = logging.getLogger(__name__)


@dataclass
class ImportSummary:
    descobertos: int = 0
    renomeados: int = 0
    duplicados: int = 0
    importados: int = 0
    falhas: int = 0
    ambiguos: int = 0


def _log(arquivo: ArquivoImportado | None, etapa: str, mensagem: str, nivel: str = LogImportacao.Nivel.INFO) -> None:
    LogImportacao.objects.create(
        arquivo_relacionado=arquivo, etapa=etapa, nivel=nivel, mensagem=mensagem
    )


def _get_or_create_tipo_jogo(nome: str) -> TipoJogo:
    tipo, _ = TipoJogo.objects.get_or_create(nome=nome)
    return tipo


def import_folder(folder: Path, *, dry_run: bool = False) -> ImportSummary:
    """Processa todos os PDFs da pasta indicada, idempotente por hash."""
    summary = ImportSummary()

    for path in discover_pdfs(folder):
        summary.descobertos += 1
        original_name = path.name

        # 1) renomeação ddmmaaaa → aaaammdd
        proposta = propose_rename(original_name)
        if proposta.ambiguous:
            summary.ambiguos += 1
            _log(
                None,
                "renomeacao",
                f"{original_name}: nome ambíguo — {proposta.motivo}",
                nivel=LogImportacao.Nivel.WARNING,
            )

        rename_result = None
        if proposta.needs_rename and not dry_run and not proposta.ambiguous:
            try:
                rename_result = apply_rename(path, proposta)
                if rename_result.moved:
                    summary.renomeados += 1
                    path = rename_result.final_path
                elif rename_result.motivo:
                    _log(
                        None,
                        "renomeacao",
                        f"{original_name}: {rename_result.motivo}",
                        nivel=LogImportacao.Nivel.WARNING,
                    )
            except OSError as exc:
                _log(
                    None,
                    "renomeacao",
                    f"{original_name}: falha ao renomear ({exc})",
                    nivel=LogImportacao.Nivel.ERROR,
                )

        nome_atual = path.name

        # 2) hash + duplicidade
        try:
            digest = file_sha256(path)
        except OSError as exc:
            summary.falhas += 1
            _log(
                None,
                "hash",
                f"{nome_atual}: falha lendo arquivo ({exc})",
                nivel=LogImportacao.Nivel.ERROR,
            )
            continue

        existing = ArquivoImportado.objects.filter(hash_arquivo=digest).first()
        if existing is not None:
            summary.duplicados += 1
            # mantém o caminho atualizado (caso o arquivo tenha sido renomeado fora)
            if existing.caminho_arquivo != str(path) or existing.nome_arquivo_atual != nome_atual:
                existing.caminho_arquivo = str(path)
                existing.nome_arquivo_atual = nome_atual
                existing.save(update_fields=["caminho_arquivo", "nome_arquivo_atual"])
            continue

        if dry_run:
            summary.importados += 1
            continue

        # 3) extração de texto
        try:
            texto_resultado = extract_text(path)
        except Exception as exc:  # noqa: BLE001
            summary.falhas += 1
            arquivo = ArquivoImportado.objects.create(
                nome_arquivo_original=original_name,
                nome_arquivo_atual=nome_atual,
                caminho_arquivo=str(path),
                hash_arquivo=digest,
                status_importacao=ArquivoImportado.Status.FALHA,
                mensagem_erro=f"extração falhou: {exc.__class__.__name__}: {exc}",
            )
            _log(
                arquivo,
                "extracao",
                str(exc),
                nivel=LogImportacao.Nivel.ERROR,
            )
            continue

        texto_normalizado = normalize(texto_resultado.texto)

        if not texto_normalizado:
            summary.falhas += 1
            arquivo = ArquivoImportado.objects.create(
                nome_arquivo_original=original_name,
                nome_arquivo_atual=nome_atual,
                caminho_arquivo=str(path),
                hash_arquivo=digest,
                quantidade_paginas=texto_resultado.paginas,
                texto_extraido="",
                status_importacao=ArquivoImportado.Status.FALHA,
                mensagem_erro="PDF sem texto selecionável (provavelmente baseado em imagem)",
            )
            _log(
                arquivo,
                "extracao",
                "texto vazio em ambos extratores; OCR seria necessário",
                nivel=LogImportacao.Nivel.WARNING,
            )
            continue

        # 4) parse + persistência
        compra = parse_compra(texto_normalizado)

        try:
            with transaction.atomic():
                arquivo = ArquivoImportado.objects.create(
                    nome_arquivo_original=original_name,
                    nome_arquivo_atual=nome_atual,
                    caminho_arquivo=str(path),
                    hash_arquivo=digest,
                    quantidade_paginas=texto_resultado.paginas,
                    texto_extraido=texto_normalizado,
                    status_importacao=ArquivoImportado.Status.EM_PROCESSAMENTO,
                    data_importacao=timezone.now(),
                )
                if texto_resultado.aviso:
                    _log(arquivo, "extracao", texto_resultado.aviso, nivel=LogImportacao.Nivel.WARNING)
                for aviso in compra.avisos:
                    _log(arquivo, "parser", aviso, nivel=LogImportacao.Nivel.WARNING)

                comprovantes_criados = 0
                for comp in compra.comprovantes:
                    tipo = _get_or_create_tipo_jogo(comp.tipo_jogo)
                    apostas_com_dezenas = sum(1 for a in comp.apostas if a.dezenas)
                    if apostas_com_dezenas == 0:
                        observacoes = (
                            "Layout novo: dezenas apostadas não constam no texto do PDF."
                        )
                    elif apostas_com_dezenas < len(comp.apostas):
                        observacoes = (
                            f"Dezenas extraídas em {apostas_com_dezenas}/{len(comp.apostas)} apostas."
                        )
                    else:
                        observacoes = ""
                    comprovante = Comprovante.objects.create(
                        arquivo_importado=arquivo,
                        tipo_jogo=tipo,
                        data_jogo=compra.data_compra,
                        valor_total_aposta=comp.valor_total,
                        codigo_autenticacao=compra.numero_compra,
                        observacoes=observacoes,
                    )
                    apostas_criadas = Aposta.objects.bulk_create(
                        [
                            Aposta(
                                comprovante=comprovante,
                                sequencia=ap.sequencia,
                                concurso=ap.concurso,
                                descricao=f"Concurso {ap.concurso}",
                                valor_aposta=ap.valor,
                            )
                            for ap in comp.apostas
                        ]
                    )
                    numeros_a_criar: list[NumeroApostado] = []
                    for aposta_obj, ap in zip(apostas_criadas, comp.apostas):
                        for ordem, numero in enumerate(ap.dezenas, start=1):
                            numeros_a_criar.append(
                                NumeroApostado(aposta=aposta_obj, ordem=ordem, numero=numero)
                            )
                    if numeros_a_criar:
                        NumeroApostado.objects.bulk_create(numeros_a_criar)
                    comprovantes_criados += 1

                if comprovantes_criados == 0:
                    arquivo.status_importacao = ArquivoImportado.Status.FALHA
                    arquivo.mensagem_erro = "Nenhum comprovante reconhecido no parser."
                else:
                    arquivo.status_importacao = ArquivoImportado.Status.SUCESSO
                arquivo.save(update_fields=["status_importacao", "mensagem_erro"])
        except Exception as exc:  # noqa: BLE001
            summary.falhas += 1
            logger.exception("Falha persistindo %s", nome_atual)
            ArquivoImportado.objects.filter(hash_arquivo=digest).update(
                status_importacao=ArquivoImportado.Status.FALHA,
                mensagem_erro=f"persistência falhou: {exc.__class__.__name__}: {exc}",
            )
            continue

        if comprovantes_criados == 0:
            summary.falhas += 1
        else:
            summary.importados += 1

    return summary
