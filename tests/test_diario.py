from app.diario import Anotacao, parse_diario, serializar_diario, inserir

_ARQUIVO = """# 📓 Diário

## 2026-07-15

- 14:32 — arrumei a cozinha (média)
- 09:10 — liguei pro dentista (leve)

## 2026-07-14

- 21:47 — refiz a lista de compras (pesada)
"""


def _anotacoes(entradas):
    return [e for e in entradas if isinstance(e, Anotacao)]


def test_parse_le_hora_texto_e_energia():
    a = _anotacoes(parse_diario(_ARQUIVO))
    assert [(x.dia, x.hora, x.texto, x.energia) for x in a] == [
        ("2026-07-15", "14:32", "arrumei a cozinha", "média"),
        ("2026-07-15", "09:10", "liguei pro dentista", "leve"),
        ("2026-07-14", "21:47", "refiz a lista de compras", "pesada"),
    ]


def test_round_trip_preserva_o_arquivo():
    assert serializar_diario(parse_diario(_ARQUIVO)) == _ARQUIVO


def test_linhas_desconhecidas_sobrevivem():
    texto = "# 📓 Diário\n\n## 2026-07-15\n\nanotei isto na mão no Obsidian\n"
    assert serializar_diario(parse_diario(texto)) == texto


def test_parenteses_no_fim_que_nao_e_energia_continua_texto():
    a = _anotacoes(parse_diario("## 2026-07-15\n\n- 10:00 — paguei a conta (de novo)\n"))
    assert a[0].texto == "paguei a conta (de novo)"
    assert a[0].energia is None


def test_anotacao_sem_energia_faz_round_trip():
    texto = "## 2026-07-15\n\n- 10:00 — paguei a conta (de novo)\n"
    assert serializar_diario(parse_diario(texto)) == texto


def test_inserir_no_arquivo_vazio_cria_cabecalho_e_dia():
    entradas = inserir(parse_diario(""), Anotacao("2026-07-15", "08:00", "acordei", "leve"))
    assert serializar_diario(entradas) == (
        "# 📓 Diário\n\n## 2026-07-15\n\n- 08:00 — acordei (leve)\n"
    )


def test_dia_novo_entra_no_topo():
    entradas = inserir(parse_diario(_ARQUIVO),
                       Anotacao("2026-07-16", "07:00", "corri", "pesada"))
    a = _anotacoes(entradas)
    assert (a[0].dia, a[0].texto) == ("2026-07-16", "corri")
    assert serializar_diario(entradas).startswith(
        "# 📓 Diário\n\n## 2026-07-16\n\n- 07:00 — corri (pesada)\n\n## 2026-07-15\n"
    )


def test_anotacao_nova_entra_no_topo_do_dia_existente():
    entradas = inserir(parse_diario(_ARQUIVO),
                       Anotacao("2026-07-15", "16:00", "reguei as plantas", "leve"))
    a = _anotacoes(entradas)
    assert [x.hora for x in a] == ["16:00", "14:32", "09:10", "21:47"]


def test_inserir_em_dia_do_meio_nao_reordena_os_outros():
    entradas = inserir(parse_diario(_ARQUIVO),
                       Anotacao("2026-07-14", "22:30", "dormi", "leve"))
    a = _anotacoes(entradas)
    assert [(x.dia, x.hora) for x in a] == [
        ("2026-07-15", "14:32"), ("2026-07-15", "09:10"),
        ("2026-07-14", "22:30"), ("2026-07-14", "21:47"),
    ]
