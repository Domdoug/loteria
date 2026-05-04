"""Parser do conteúdo textual extraído dos PDFs de compra de apostas da Caixa.

Reconhece três layouts:

**Layout novo (~2024+):** coluna "Situação da Aposta" entre Concurso e Valor.
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

**Layout OCR (PDFs imagem):** texto extraído via OCR com row-sorting por (y, x).
    Cada linha combina status + dezenas? + concurso + R$ + dezenas_tail?.
    Cabeçalhos de jogo aparecem com palavras da tabela em ordem aleatória.

    de da Valor da Mega-Sena Concurso Aposta Aposta Situação
    Efetivada 18 26 33 37 40 48 3000 R$ 6,00

A coluna "Situação da Aposta" é descartada no domínio: todos os comprovantes
nesses PDFs estão efetivados.
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
# OCR row-sorted: palavras embaralhadas na linha.
# Dois subformatos observados:
#   2026: "da Data 25/04/2026 Compra:"  → Data ANTES da data
#   2023: "13/04/2024 Data da Compra:"  → data ANTES de Data
_DATA_OCR_RE = re.compile(r"\bData\b[^/\n]*?(\d{2})/(\d{2})/(\d{4})", re.IGNORECASE)
_DATA_OCR_REVERSED_RE = re.compile(r"(\d{2})/(\d{2})/(\d{4})[^\n]*\bCompra\b", re.IGNORECASE)
_NUMERO_OCR_RE = re.compile(r"\bN[uú]mero\b[^\n]*?\b(\d{5,})\b", re.IGNORECASE)

# OCR layout: linha de aposta começa com status.
# Dois subformatos observados:
#   2024: Efetivada [dezenas] <concurso> R$ <valor>
#   2025: Efetivada R$ [dezenas] <concurso> <valor>   (R$ logo após status)
# Regex unificado: consome R$ opcional logo após status, depois middle não-greedy
# até encontrar a primeira string "N,NN" que é o valor.
_OCR_VALOR_RE = re.compile(
    r"^(?:Efetivada|Em\s+Processamento|N[aã]o\s+Efetivada)\s+"
    r"(?:R\$\s+)?"           # R$ opcional logo após o status (2025)
    r"(?P<middle>.*?)"
    r"(?:R\$\s*)?"           # R$ opcional antes do valor (2024)
    r"(?P<valor>[\d.]+,\d{2})"
    r"(?P<tail>.*)$",
    re.IGNORECASE,
)

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

# Dezenas esperadas por tipo de jogo (para detecção de continuação no OCR)
_DEZENAS_ESPERADAS: dict[str, int] = {
    "Mega-Sena": 6,
    "Lotofácil": 15,
    "Quina": 5,
    "Lotomania": 20,
    "Timemania": 10,
    "Dupla-Sena": 6,
    "Dia de Sorte": 7,
    "+Milionária": 6,
    "Super Sete": 7,
}

# Meses em português para ignorar nas linhas do Dia de Sorte
_MESES_PT = {
    "JANEIRO", "FEVEREIRO", "MARCO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO",
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


def _nums_e_concurso(text: str) -> tuple[list[int], str | None]:
    """Extrai dezenas (1-2 dígitos) e concurso (3+ dígitos) de uma string."""
    tokens = text.split()
    digits = [(i, t) for i, t in enumerate(tokens) if t.isdigit()]

    # Último número com 3+ dígitos = concurso
    concurso: str | None = None
    concurso_pos: int | None = None
    for i, (_, t) in enumerate(digits):
        if len(t) >= 3:
            concurso = t
            concurso_pos = i

    if concurso is None:
        return [], None

    dezenas = [int(t) for _, t in digits[:concurso_pos] if len(t) <= 2]
    return dezenas, concurso


def _extract_ocr_dezenas(linha: str) -> list[int]:
    """Extrai números 1-2 dígitos de uma linha, tolerando tokens não-numéricos (OCR noise)."""
    return [int(t) for t in linha.split() if t.isdigit() and 1 <= len(t) <= 2]


def _is_mostly_numbers(linha: str) -> bool:
    """True se mais da metade dos tokens forem números 1-2 dígitos."""
    tokens = [t for t in linha.split() if t.strip()]
    if not tokens:
        return False
    num_count = sum(1 for t in tokens if t.isdigit() and len(t) <= 2)
    return num_count >= max(2, len(tokens) * 0.5)


def _find_jogo_nome(linha: str) -> str | None:
    """Retorna o nome canônico do jogo se a linha contiver um jogo conhecido.

    Aceita tanto substring exata quanto todas as palavras do nome presentes na linha
    (para headers OCR com palavras embaralhadas, ex: 'da Dia Sorte Concurso').
    """
    # normaliza hifens para espaço: "mega-sena" → "mega sena"
    normalizado = strip_accents(linha).lower().replace("-", " ")
    tokens = set(normalizado.split())
    for chave, nome in JOGOS_CONHECIDOS.items():
        chave_norm = chave.replace("-", " ")
        if chave_norm in normalizado:
            return nome
        # fallback: todas as palavras do nome estão presentes (qualquer ordem)
        chave_words = set(chave_norm.split())
        if len(chave_words) >= 1 and chave_words.issubset(tokens):
            return nome
    return None


def parse_compra(texto: str) -> CompraExtraida:
    """Tenta parser regular primeiro; cai no parser OCR se não encontrar comprovantes."""
    resultado = _parse_regular(texto)
    if not resultado.comprovantes:
        resultado = _parse_ocr(texto)
    return resultado


def _parse_regular(texto: str) -> CompraExtraida:
    """Parser para layouts textual antigo (~2022) e novo (~2024+)."""
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

    compra.comprovantes = [c for c in compra.comprovantes if c.apostas]
    if not compra.comprovantes:
        compra.avisos.append("nenhum comprovante com apostas reconhecidas")
    return compra


def _parse_ocr(texto: str) -> CompraExtraida:
    """Parser para texto extraído via OCR com row-sorting (PDFs imagem).

    Cada linha de aposta tem o formato:
      Efetivada [dezenas_head] <concurso> R$ <valor> [dezenas_tail]

    Dezenas podem aparecer em linhas separadas antes (pré-commit) ou
    depois (continuação) da linha de aposta.
    """
    compra = CompraExtraida()

    m = _NUMERO_COMPRA_RE.search(texto) or _NUMERO_OCR_RE.search(texto)
    if m:
        compra.numero_compra = m.group(1)

    m = (
        _DATA_COMPRA_RE.search(texto)
        or _DATA_ANTIGA_RE.search(texto)
        or _DATA_OCR_RE.search(texto)
        or _DATA_OCR_REVERSED_RE.search(texto)
    )
    if m:
        compra.data_compra = _parse_data(m.group(1), m.group(2), m.group(3))
        if compra.data_compra is None:
            compra.avisos.append(f"data inválida: {m.group(0)!r}")

    comprovante: ComprovanteExtraido | None = None
    buffer_dezenas: list[int] = []
    last_aposta: ApostaExtraida | None = None
    pending_dezenas = 0
    sequencia_global = 0

    def commit_aposta(dezenas_head: list[int], concurso: str, valor: str, dezenas_tail: list[int]) -> ApostaExtraida:
        nonlocal sequencia_global, buffer_dezenas, pending_dezenas
        all_dezenas = tuple(buffer_dezenas + dezenas_head + dezenas_tail)
        sequencia_global += 1
        ap = ApostaExtraida(
            sequencia=sequencia_global,
            concurso=concurso,
            valor=_parse_valor(valor),
            dezenas=all_dezenas,
        )
        assert comprovante is not None
        comprovante.apostas.append(ap)

        esperadas = _DEZENAS_ESPERADAS.get(comprovante.tipo_jogo, 0)
        pending_dezenas = max(0, esperadas - len(all_dezenas)) if esperadas else 0
        buffer_dezenas = []
        return ap

    for raw in texto.splitlines():
        linha = raw.strip()
        if not linha:
            continue

        # Ignorar meses (Dia de Sorte) e cidades com "/" (Timemania)
        linha_upper = strip_accents(linha).upper()
        if linha_upper in _MESES_PT or "/" in linha:
            continue

        # Cabeçalho de jogo: linha contém nome do jogo + "Concurso" (coluna da tabela)
        jogo_nome = _find_jogo_nome(linha)
        if jogo_nome:
            linha_norm = strip_accents(linha).lower()
            if "concurso" in linha_norm:
                comprovante = ComprovanteExtraido(
                    tipo_jogo_bruto=jogo_nome,
                    tipo_jogo=jogo_nome,
                )
                compra.comprovantes.append(comprovante)
                buffer_dezenas = []
                last_aposta = None
                pending_dezenas = 0
                continue

        if comprovante is None:
            continue

        # Linha de aposta: começa com status, contém R$ valor
        m_ocr = _OCR_VALOR_RE.match(linha)
        if m_ocr:
            middle = m_ocr.group("middle") or ""
            tail = m_ocr.group("tail") or ""
            valor_str = m_ocr.group("valor")

            dezenas_head, concurso = _nums_e_concurso(middle)
            dezenas_tail = _extract_ocr_dezenas(tail)

            if concurso:
                last_aposta = commit_aposta(dezenas_head, concurso, valor_str, dezenas_tail)
            continue

        # Linha de dezenas (maioria números 1-2 dígitos)
        if _is_mostly_numbers(linha):
            nums = _extract_ocr_dezenas(linha)
            if nums:
                # Continuação: só se precisamos de dezenas E a linha não tem mais do que o esperado.
                # Se a linha tiver MAIS dezenas do que o pending, é o pré-commit da próxima aposta.
                if pending_dezenas > 0 and last_aposta is not None and len(nums) <= pending_dezenas:
                    updated = ApostaExtraida(
                        sequencia=last_aposta.sequencia,
                        concurso=last_aposta.concurso,
                        valor=last_aposta.valor,
                        dezenas=last_aposta.dezenas + tuple(nums),
                    )
                    comprovante.apostas[-1] = updated
                    last_aposta = updated
                    pending_dezenas -= len(nums)
                else:
                    buffer_dezenas.extend(nums)
                    last_aposta = None
                    pending_dezenas = 0

    compra.comprovantes = [c for c in compra.comprovantes if c.apostas]
    if not compra.comprovantes:
        compra.avisos.append("nenhum comprovante com apostas reconhecidas (OCR)")
    return compra
