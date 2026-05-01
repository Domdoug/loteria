"""Parser do conteúdo textual extraído dos PDFs de compra de apostas da Caixa.

Reconhece dois layouts observados no histórico:

**Layout novo (~2024+):** uma coluna "Situação da Aposta" entre Concurso e Valor.
    Cada aposta cabe em uma única linha; as dezenas NÃO aparecem no texto.

    Mega-Sena Concurso Situação da Aposta Valor da Aposta
    2731 Efetivada R$ 5,00

**Layout antigo (~2022):** sem a coluna "Situação". Cada aposta ocupa três linhas:
    a linha das dezenas (pode quebrar em mais de uma), a linha
    `<concurso> R$ <valor>`, e o marcador ` Aposta efetivada!`.

    Mega-Sena Concurso Valor da Aposta
    18 33 34 39 49 56
    2543 R$ 4,50
     Aposta efetivada!

A coluna "Situação da Aposta" é descartada no domínio: todos os comprovantes
nesses PDFs estão efetivados.

Limitação conhecida — Super Sete: a primeira linha de cada aposta no layout
antigo é o cabeçalho fixo de colunas (`11 22 33 44 55 66 77`); os dígitos
escolhidos vêm DEPOIS do `<concurso> R$ <valor>`. O parser filtra o cabeçalho
mas não captura os dígitos escolhidos do Super Sete (impacto: ~2 comprovantes
no histórico atual).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from .normalizer import strip_accents

_HEADER_RE = re.compile(
    r"^(?P<jogo>[^\n]+?)\s+Concurso\s+(?:Situ[aã][cç][aã]o\s+da\s+Aposta\s+)?Valor\s+da\s+Aposta\s*$",
    re.IGNORECASE,
)

_APOSTA_NOVO_RE = re.compile(
    r"^(?P<concurso>\d+)\s+(?:Efetivada|Em\s+Processamento|N[aã]o\s+Efetivada)"
    r"\s+R\$\s*(?P<valor>[\d.]+,\d{2})\s*$",
    re.IGNORECASE,
)

_APOSTA_ANTIGO_RE = re.compile(
    r"^(?P<concurso>\d+)\s+R\$\s*(?P<valor>[\d.]+,\d{2})\s*$",
)

_APOSTA_EFETIVADA_RE = re.compile(r"^Aposta\s+efetivada!?$", re.IGNORECASE)

# Linha contendo apenas números (1-2 dígitos) separados por espaço
_NUM_LINE_RE = re.compile(r"^\d{1,2}(?:\s+\d{1,2})+$")

# Cabeçalho fixo do Super Sete no layout antigo — não são dezenas escolhidas
_SUPER_SETE_HEADER = "11 22 33 44 55 66 77"

_DATA_COMPRA_RE = re.compile(r"Data\s+da\s+Compra:\s*(\d{2})/(\d{2})/(\d{4})", re.IGNORECASE)
_NUMERO_COMPRA_RE = re.compile(r"N[uú]mero\s+da\s+Compra:\s*(\S+)", re.IGNORECASE)
# Layout antigo expõe a data como "Hora DF: HH:MM:SS Data: dd/mm/aaaa"
_DATA_ANTIGA_RE = re.compile(r"Data:\s*(\d{2})/(\d{2})/(\d{4})", re.IGNORECASE)


JOGOS_CONHECIDOS = {
    "mega-sena": "Mega-Sena",
    "lotofacil": "Lotofácil",
    "quina": "Quina",
    "lotomania": "Lotomania",
    "timemania": "Timemania",
    "dupla-sena": "Dupla-Sena",
    "dia de sorte": "Dia de Sorte",
    "dia da sorte": "Dia de Sorte",
    "+milionaria": "+Milionária",
    "super sete": "Super Sete",
    "loteca": "Loteca",
    "lotogol": "Lotogol",
}


@dataclass
class ApostaExtraida:
    sequencia: int
    concurso: str
    valor: Decimal
    dezenas: tuple[int, ...] = ()


@dataclass
class ComprovanteExtraido:
    tipo_jogo_bruto: str
    tipo_jogo: str  # canonizado
    apostas: list[ApostaExtraida] = field(default_factory=list)

    @property
    def valor_total(self) -> Decimal:
        return sum((a.valor for a in self.apostas), start=Decimal("0"))


@dataclass
class CompraExtraida:
    numero_compra: str = ""
    data_compra: date | None = None
    comprovantes: list[ComprovanteExtraido] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)


def _canonicalize(jogo_bruto: str) -> str:
    chave = strip_accents(jogo_bruto).strip().lower()
    return JOGOS_CONHECIDOS.get(chave, jogo_bruto.strip())


def _parse_valor(s: str) -> Decimal:
    return Decimal(s.replace(".", "").replace(",", "."))


def _parse_data(d: str, m: str, y: str) -> date | None:
    try:
        return datetime.strptime(f"{d}/{m}/{y}", "%d/%m/%Y").date()
    except ValueError:
        return None


def _flush_dezenas(buffer: list[str]) -> tuple[int, ...]:
    """Junta as linhas de números acumuladas em uma sequência de dezenas."""
    nums: list[int] = []
    for linha in buffer:
        if linha == _SUPER_SETE_HEADER:
            continue
        for token in linha.split():
            if token.isdigit():
                nums.append(int(token))
    return tuple(nums)


def parse_compra(texto: str) -> CompraExtraida:
    compra = CompraExtraida()

    m = _NUMERO_COMPRA_RE.search(texto)
    if m:
        compra.numero_compra = m.group(1)

    m = _DATA_COMPRA_RE.search(texto) or _DATA_ANTIGA_RE.search(texto)
    if m:
        compra.data_compra = _parse_data(m.group(1), m.group(2), m.group(3))
        if compra.data_compra is None:
            compra.avisos.append(f"data inválida: {m.group(0)!r}")

    comprovante: ComprovanteExtraido | None = None
    buffer_dezenas: list[str] = []
    sequencia_global = 0

    def add_aposta(concurso: str, valor: str, dezenas: tuple[int, ...]) -> None:
        nonlocal sequencia_global
        if comprovante is None:
            return
        sequencia_global += 1
        comprovante.apostas.append(
            ApostaExtraida(
                sequencia=sequencia_global,
                concurso=concurso,
                valor=_parse_valor(valor),
                dezenas=dezenas,
            )
        )

    for raw in texto.splitlines():
        linha = raw.strip()
        if not linha:
            continue

        if linha.lower().startswith("total") or linha.lower().startswith("valor total"):
            comprovante = None
            buffer_dezenas = []
            continue

        m = _HEADER_RE.match(linha)
        if m:
            jogo_bruto = m.group("jogo").strip()
            comprovante = ComprovanteExtraido(
                tipo_jogo_bruto=jogo_bruto,
                tipo_jogo=_canonicalize(jogo_bruto),
            )
            compra.comprovantes.append(comprovante)
            buffer_dezenas = []
            continue

        if comprovante is None:
            continue

        m_novo = _APOSTA_NOVO_RE.match(linha)
        if m_novo:
            add_aposta(m_novo.group("concurso"), m_novo.group("valor"), ())
            buffer_dezenas = []
            continue

        m_antigo = _APOSTA_ANTIGO_RE.match(linha)
        if m_antigo:
            dezenas = _flush_dezenas(buffer_dezenas)
            add_aposta(m_antigo.group("concurso"), m_antigo.group("valor"), dezenas)
            buffer_dezenas = []
            continue

        if _APOSTA_EFETIVADA_RE.match(linha):
            buffer_dezenas = []
            continue

        if _NUM_LINE_RE.match(linha):
            buffer_dezenas.append(linha)
            continue

        # outras linhas (nome de time da Timemania, dígitos do Super Sete, etc.):
        # descartadas — não impactam o domínio extraído.

    compra.comprovantes = [c for c in compra.comprovantes if c.apostas]
    if not compra.comprovantes:
        compra.avisos.append("nenhum comprovante com apostas reconhecidas")
    return compra
