"""Testa o upload de XLSX via view atualizar_megasena."""

from __future__ import annotations

import io
from datetime import date

import pytest

openpyxl = pytest.importorskip("openpyxl")

from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402

from resultados.models import ResultadoMegaSena  # noqa: E402


def _xlsx_bytes() -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(["Concurso", "Data do Sorteio", "Bola1", "Bola2", "Bola3", "Bola4", "Bola5", "Bola6"])
    ws.append([9001, date(2026, 5, 7), 3, 12, 25, 38, 47, 60])
    ws.append([9002, "08/05/2026", 1, 2, 3, 4, 5, 6])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.django_db
def test_upload_xlsx_cria_resultados():
    client = Client()
    url = reverse("resultados:atualizar_megasena")
    uploaded = SimpleUploadedFile("mega.xlsx", _xlsx_bytes(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    response = client.post(url, {"xlsx": uploaded})

    assert response.status_code == 302
    assert response["Location"].rstrip("/") in ("", "/")
    assert ResultadoMegaSena.objects.filter(concurso=9001).exists()
    assert ResultadoMegaSena.objects.filter(concurso=9002).exists()


@pytest.mark.django_db
def test_upload_sem_arquivo_redireciona():
    client = Client()
    url = reverse("resultados:atualizar_megasena")
    response = client.post(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_upload_extensao_invalida_redireciona():
    client = Client()
    url = reverse("resultados:atualizar_megasena")
    uploaded = SimpleUploadedFile("dados.csv", b"not xlsx", content_type="text/csv")
    response = client.post(url, {"xlsx": uploaded})
    assert response.status_code == 302
