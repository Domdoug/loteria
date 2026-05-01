from importacao.services.file_rename import propose_rename


def test_rename_ddmmaaaa_basico():
    p = propose_rename("01062024.pdf")
    assert p.needs_rename is True
    assert p.ambiguous is False
    assert p.new_name == "20240601.pdf"


def test_rename_preserva_sufixo():
    p = propose_rename("05112024_pt1.pdf")
    assert p.needs_rename is True
    assert p.new_name == "20241105_pt1.pdf"


def test_aaaammdd_nao_renomeia():
    p = propose_rename("20240601.pdf")
    assert p.needs_rename is False
    assert p.ambiguous is False


def test_data_invalida_ambiguo():
    p = propose_rename("99992024.pdf")
    assert p.ambiguous is True


def test_nome_fora_do_padrao_ambiguo():
    p = propose_rename("relatorio.pdf")
    assert p.ambiguous is True
