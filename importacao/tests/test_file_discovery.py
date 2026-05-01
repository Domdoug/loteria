from pathlib import Path

from importacao.services.file_discovery import discover_pdfs


def test_discover_pdfs_filtra_por_extensao(tmp_path: Path):
    (tmp_path / "a.pdf").write_bytes(b"x")
    (tmp_path / "B.PDF").write_bytes(b"x")
    (tmp_path / "ignore.txt").write_text("nope")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "skipped.pdf").write_bytes(b"x")

    achados = sorted(p.name.lower() for p in discover_pdfs(tmp_path))
    assert achados == ["a.pdf", "b.pdf"]


def test_discover_pdfs_pasta_inexistente(tmp_path: Path):
    achados = list(discover_pdfs(tmp_path / "nao_existe"))
    assert achados == []
