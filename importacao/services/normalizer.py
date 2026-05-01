"""Normalização do texto extraído antes do parsing."""

import re
import unicodedata


def strip_accents(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def normalize(texto: str) -> str:
    """Normaliza espaços, quebras de linha repetidas e caracteres invisíveis.

    Mantém acentos no texto original; o parser usa `strip_accents` quando precisa
    comparar nomes de jogos.
    """
    if not texto:
        return ""
    # remove caracteres de controle (exceto \n)
    texto = "".join(ch for ch in texto if ch == "\n" or ch >= " ")
    # normaliza espaços horizontais
    texto = re.sub(r"[\t\f\v ]+", " ", texto)
    # colapsa quebras múltiplas
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    # tira espaços nas pontas de cada linha
    texto = "\n".join(linha.strip() for linha in texto.splitlines())
    return texto.strip()
