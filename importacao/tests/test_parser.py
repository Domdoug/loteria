from decimal import Decimal

from importacao.services.parser import parse_compra

PDF_TEXT_NOVO = """\
Pagamento processado por:
Número da Compra: 212439893
Situação da Compra: Finalizada - Todas as apostas efetivadas
Data da Compra: 01/06/2024
Hora da Compra: 17:48:03
+Milionária Concurso Situação da Aposta Valor da Aposta
151 Efetivada R$ 6,00
151 Efetivada R$ 6,00
Mega-Sena Concurso Situação da Aposta Valor da Aposta
2731 Efetivada R$ 5,00
2731 Efetivada R$ 5,00
2731 Efetivada R$ 5,00
Total da Compra: R$ 27,00
"""

PDF_TEXT_ANTIGO = """\
Aposte online no Super Sete https://www.loteriasonline.caixa.gov.br/...
Hora DF: 14:48:56 Data: 19/11/2022
Mega-Sena Concurso Valor da Aposta
14 16 20 22 38 41
2540 R$ 4,50
 Aposta efetivada!
17 31 35 39 46 55
2540 R$ 4,50
 Aposta efetivada!
Quina Concurso Valor da Aposta
23 49 58 72 80
6003 R$ 2,00
 Aposta efetivada!
Timemania Concurso Valor da Aposta
03 12 18 20 28 29 37 38
52 61
1862 R$ 3,00
ATLETICO/CE
 Aposta efetivada!
Valor total das apostas: R$ 14,00
"""


def test_parser_extrai_layout_novo():
    compra = parse_compra(PDF_TEXT_NOVO)
    assert compra.numero_compra == "212439893"
    assert compra.data_compra.day == 1
    assert len(compra.comprovantes) == 2
    milionaria, mega = compra.comprovantes
    assert milionaria.tipo_jogo == "+Milionária"
    assert milionaria.valor_total == Decimal("12.00")
    assert mega.valor_total == Decimal("15.00")
    # Layout novo: dezenas vazias
    assert all(a.dezenas == () for a in mega.apostas)


def test_parser_extrai_layout_antigo_com_dezenas():
    compra = parse_compra(PDF_TEXT_ANTIGO)
    assert compra.data_compra.year == 2022
    assert compra.data_compra.month == 11
    assert len(compra.comprovantes) == 3

    mega, quina, timemania = compra.comprovantes
    assert mega.tipo_jogo == "Mega-Sena"
    assert len(mega.apostas) == 2
    assert mega.apostas[0].concurso == "2540"
    assert mega.apostas[0].dezenas == (14, 16, 20, 22, 38, 41)
    assert mega.apostas[1].dezenas == (17, 31, 35, 39, 46, 55)
    assert mega.valor_total == Decimal("9.00")

    assert quina.apostas[0].dezenas == (23, 49, 58, 72, 80)

    # Timemania quebra dezenas em 2 linhas; o parser deve uni-las.
    assert timemania.apostas[0].dezenas == (3, 12, 18, 20, 28, 29, 37, 38, 52, 61)


def test_parser_sem_apostas_emite_aviso():
    compra = parse_compra("Pagamento processado por: nada aqui")
    assert compra.comprovantes == []
    assert any("nenhum comprovante" in a.lower() for a in compra.avisos)


def test_parser_filtra_super_sete_header():
    """O cabeçalho '11 22 33 44 55 66 77' do Super Sete não deve virar dezenas."""
    texto = """\
Hora DF: 18:05:55 Data: 26/11/2022
Super Sete Concurso Valor da Aposta
11 22 33 44 55 66 77
325 R$ 2,50
 Aposta efetivada!
Valor total das apostas: R$ 2,50
"""
    compra = parse_compra(texto)
    assert len(compra.comprovantes) == 1
    aposta = compra.comprovantes[0].apostas[0]
    assert aposta.concurso == "325"
    assert aposta.dezenas == ()  # cabeçalho do Super Sete foi descartado
