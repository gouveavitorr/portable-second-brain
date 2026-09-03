from app.tasks import (
    Tarefa,
    parse_tarefas,
    serializar_tarefas,
    serializar_linha,
    gerar_id,
    garantir_ids,
)


def test_parse_linha_completa():
    linha = ("- [ ] Escrever a introdução | prioridade:alta | energia:pesada "
             "| passo: abrir o doc e escrever a 1ª frase | prazo:2026-07-15 | id:a1b2")
    (t,) = parse_tarefas(linha)
    assert isinstance(t, Tarefa)
    assert t.concluida is False
    assert t.titulo == "Escrever a introdução"
    assert t.prioridade == "alta"
    assert t.energia == "pesada"
    assert t.passo == "abrir o doc e escrever a 1ª frase"
    assert t.prazo == "2026-07-15"
    assert t.id == "a1b2"


def test_parse_linha_minima():
    (t,) = parse_tarefas("- [ ] fazer X")
    assert t.titulo == "fazer X"
    assert t.concluida is False
    assert t.id is None
    assert t.prioridade is None


def test_parse_concluida():
    (t,) = parse_tarefas("- [x] Lavar a louça | id:e5f6")
    assert t.concluida is True
    assert t.titulo == "Lavar a louça"


def test_parse_min_vira_int():
    (t,) = parse_tarefas("- [ ] X | min:30")
    assert t.min == 30


def test_linhas_nao_tarefa_preservadas():
    texto = "# Minhas tarefas\n\n- [ ] fazer X | id:aaaa\ntexto solto"
    entradas = parse_tarefas(texto)
    assert entradas[0] == "# Minhas tarefas"
    assert entradas[1] == ""
    assert isinstance(entradas[2], Tarefa)
    assert entradas[3] == "texto solto"


def test_serializar_linha_canonica():
    t = Tarefa(titulo="X", prioridade="alta", energia="leve", id="a1b2")
    assert serializar_linha(t) == "- [ ] X | prioridade:alta | energia:leve | id:a1b2"


def test_round_trip_idempotente():
    texto = ("# cabeçalho\n\n"
             "- [ ] Escrever intro | prioridade:alta | energia:pesada | passo: abrir o doc | prazo:2026-07-15 | id:a1b2\n"
             "- [x] Lavar louça | prioridade:baixa | energia:leve | id:e5f6\n"
             "linha solta\n")
    entradas = parse_tarefas(texto)
    saida1 = serializar_tarefas(entradas)
    saida2 = serializar_tarefas(parse_tarefas(saida1))
    assert saida1 == saida2
    assert saida1.splitlines()[0] == "# cabeçalho"
    assert "linha solta" in saida1.splitlines()


def test_gerar_id_curto_e_hex():
    i = gerar_id()
    assert len(i) == 4
    int(i, 16)


def test_garantir_ids_atribui_a_quem_falta():
    entradas = parse_tarefas("- [ ] sem id\n- [ ] com id | id:aaaa")
    mudou = garantir_ids(entradas)
    assert mudou is True
    assert entradas[0].id is not None and len(entradas[0].id) == 4
    assert entradas[1].id == "aaaa"
    assert garantir_ids(entradas) is False
