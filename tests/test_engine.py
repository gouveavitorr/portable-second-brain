from datetime import date
from app.tasks import Tarefa
from app.engine import escolher_agora


def _t(titulo, **kw):
    return Tarefa(titulo=titulo, **kw)


def test_exclui_concluidas():
    tarefas = [_t("a", concluida=True), _t("b")]
    r = escolher_agora(tarefas, hoje=date(2026, 7, 14))
    assert [t.titulo for t in r] == ["b"]


def test_ordena_prazo_vencido_primeiro():
    tarefas = [
        _t("sem prazo"),
        _t("vencida", prazo="2026-07-10"),
        _t("hoje", prazo="2026-07-14"),
        _t("futura", prazo="2026-07-20"),
    ]
    r = escolher_agora(tarefas, hoje=date(2026, 7, 14), n=4)
    titulos = [t.titulo for t in r]
    assert titulos.index("vencida") < titulos.index("futura")
    assert titulos.index("hoje") < titulos.index("futura")
    assert titulos.index("futura") < titulos.index("sem prazo")


def test_ordena_por_prioridade():
    tarefas = [_t("baixa", prioridade="baixa"),
               _t("alta", prioridade="alta"),
               _t("media", prioridade="media")]
    r = escolher_agora(tarefas, hoje=date(2026, 7, 14), n=3)
    assert [t.titulo for t in r] == ["alta", "media", "baixa"]


def test_modo_facil_prioriza_leves_e_rapidas():
    tarefas = [_t("pesada", energia="pesada", prioridade="alta"),
               _t("leve curta", energia="leve", min=5),
               _t("leve longa", energia="leve", min=60)]
    r = escolher_agora(tarefas, hoje=date(2026, 7, 14), modo_facil=True, n=3)
    assert [t.titulo for t in r] == ["leve curta", "leve longa", "pesada"]


def test_devolve_no_maximo_n():
    tarefas = [_t(str(i)) for i in range(10)]
    r = escolher_agora(tarefas, hoje=date(2026, 7, 14), n=3)
    assert len(r) == 3


def test_menos_que_n_devolve_todas_sem_repetir():
    tarefas = [_t("a"), _t("b")]
    r = escolher_agora(tarefas, hoje=date(2026, 7, 14), n=3)
    assert [t.titulo for t in r] == ["a", "b"]


def test_paginacao_avanca_e_cicla():
    tarefas = [_t("a", prioridade="alta"), _t("b", prioridade="alta"),
               _t("c", prioridade="alta"), _t("d", prioridade="alta")]
    p0 = [t.titulo for t in escolher_agora(tarefas, hoje=date(2026, 7, 14), offset=0, n=3)]
    p1 = [t.titulo for t in escolher_agora(tarefas, hoje=date(2026, 7, 14), offset=3, n=3)]
    assert p0 == ["a", "b", "c"]
    assert p1 == ["d", "a", "b"]
