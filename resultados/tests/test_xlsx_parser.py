from datetime import date
from pathlib import Path

import pytest

openpyxl = pytest.importorskip("openpyxl")

from resultados.services.megasena_importer import parse_xlsx_megasena  # noqa: E402


def _criar_xlsx_fixture(path: Path) -> None:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "MEGA SENA"
    ws.append(
        [
            "Concurso",
            "Data do Sorteio",
            "Bola1",
            "Bola2",
            "Bola3",
            "Bola4",
            "Bola5",
            "Bola6",
            "Ganhadores 6 acertos",
        ]
    )
    ws.append([1, "11/03/1996", 4, 5, 30, 33, 41, 52, 0])
    ws.append([2, date(1996, 3, 18), 9, 37, 39, 41, 43, 49, 1])
    ws.append([None, None, None, None, None, None, None, None, None])  # linha vazia
    ws.append([3002, "30/04/2026", 4, 27, 51, 52, 54, 58, 1])
    wb.save(path)


def test_parse_xlsx_extrai_resultados(tmp_path: Path):
    fixture = tmp_path / "mega.xlsx"
    _criar_xlsx_fixture(fixture)

    resultados = parse_xlsx_megasena(fixture)
    assert len(resultados) == 3
    assert resultados[0].concurso == 1
    assert resultados[0].data == date(1996, 3, 11)
    assert resultados[0].dezenas == (4, 5, 30, 33, 41, 52)
    assert resultados[1].data == date(1996, 3, 18)  # data como objeto date
    assert resultados[2].concurso == 3002
    assert resultados[2].dezenas == (4, 27, 51, 52, 54, 58)
