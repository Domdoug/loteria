"""Renomeação segura de PDFs do formato ddmmaaaa para aaaammdd.

Regras (do CLAUDE.md):
- nunca sobrescrever arquivos existentes
- registrar nome original e nome novo
- sinalizar casos ambíguos para revisão manual
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

# Aceita: ddmmaaaa.pdf  ou  ddmmaaaa_<sufixo>.pdf  (ex.: 05112024_pt1.pdf)
_DDMMAAAA_RE = re.compile(r"^(?P<dd>\d{2})(?P<mm>\d{2})(?P<aaaa>\d{4})(?P<sufixo>(?:_[^.]+)?)\.pdf$", re.IGNORECASE)
# Aceita: aaaammdd.pdf  ou  aaaammdd_<sufixo>.pdf  (já no formato alvo)
_AAAAMMDD_RE = re.compile(r"^(?P<aaaa>\d{4})(?P<mm>\d{2})(?P<dd>\d{2})(?P<sufixo>(?:_[^.]+)?)\.pdf$", re.IGNORECASE)


@dataclass(frozen=True)
class RenameProposal:
    original_name: str
    new_name: str
    needs_rename: bool
    ambiguous: bool
    motivo: str = ""


def _try_date(aaaa: str, mm: str, dd: str) -> date | None:
    try:
        return date(int(aaaa), int(mm), int(dd))
    except ValueError:
        return None


def propose_rename(original_name: str) -> RenameProposal:
    """Avalia o nome do arquivo e devolve a proposta de renomeação.

    Não toca o disco; apenas calcula o nome alvo e indica ambiguidade.
    """
    name = original_name

    m = _AAAAMMDD_RE.match(name)
    if m and _try_date(m["aaaa"], m["mm"], m["dd"]):
        return RenameProposal(
            original_name=name, new_name=name, needs_rename=False, ambiguous=False
        )

    m = _DDMMAAAA_RE.match(name)
    if m:
        d = _try_date(m["aaaa"], m["mm"], m["dd"])
        if d:
            new_name = f"{m['aaaa']}{m['mm']}{m['dd']}{m['sufixo']}.pdf"
            return RenameProposal(
                original_name=name,
                new_name=new_name,
                needs_rename=new_name.lower() != name.lower(),
                ambiguous=False,
            )
        return RenameProposal(
            original_name=name,
            new_name=name,
            needs_rename=False,
            ambiguous=True,
            motivo="data inválida (dd/mm/aaaa não forma data real)",
        )

    return RenameProposal(
        original_name=name,
        new_name=name,
        needs_rename=False,
        ambiguous=True,
        motivo="nome fora do padrão ddmmaaaa[_sufixo].pdf",
    )


@dataclass(frozen=True)
class RenameResult:
    moved: bool
    final_path: Path
    motivo: str = ""


def apply_rename(path: Path, proposal: RenameProposal) -> RenameResult:
    """Renomeia o arquivo seguindo a proposta, sem sobrescrever existentes.

    - Se o destino já existe, não move e devolve `moved=False` com motivo.
    - O caller é responsável por persistir nome_original/nome_atual no banco.
    """
    if not proposal.needs_rename or proposal.ambiguous:
        return RenameResult(moved=False, final_path=path, motivo=proposal.motivo or "sem alteração")

    target = path.with_name(proposal.new_name)
    if target.exists():
        return RenameResult(
            moved=False,
            final_path=path,
            motivo=f"alvo {proposal.new_name} já existe — renomeação ignorada",
        )

    path.rename(target)
    return RenameResult(moved=True, final_path=target)
