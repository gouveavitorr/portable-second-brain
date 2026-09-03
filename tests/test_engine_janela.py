"""Testes do motor 'Agora' com consciência de tempo (Fase 2)."""
from datetime import date
from app.tasks import Tarefa
from app.engine import escolher_agora, cabe_na_janela, MIN_ESTIMADO

HOJE = date(2026, 7, 14)


def _t(titulo, **kw):
    return Tarefa(titulo=titulo, **kw)


def test_min_estimado_por_energia():
    assert MIN_ESTIMADO["leve"] < MIN_ESTIMADO["media"] < MIN_ESTIMADO["pesada"]


def test_cabe_usa_min_explicito_quando_existe():
    assert cabe_na_janela(_t("x", min=20), janela=30) is True
    assert cabe_na_janela(_t("x", min=40), janela=30) is False


def test_cabe_min_explicito_ganha_da_energia():
    # tarefa pesada mas curta: o min explícito manda
    assert cabe_na_janela(_t("x", energia="pesada", min=5), janela=10) is True


def test_cabe_estima_pela_energia_sem_min():
    assert cabe_na_janela(_t("x", energia="leve"), janela=15) is True
    assert cabe_na_janela(_t("x", energia="pesada"), janela=15) is False


def test_cabe_sem_energia_usa_media():
    assert cabe_na_janela(_t("x"), janela=MIN_ESTIMADO["media"]) is True
    assert cabe_na_janela(_t("x"), janela=MIN_ESTIMADO["media"] - 1) is False


def test_cabe_janela_none_e_ilimitada():
    assert cabe_na_janela(_t("x", energia="pesada", min=999), janela=None) is True


def test_janela_curta_esconde_pesadas():
    tarefas = [_t("pesada", energia="pesada", prioridade="alta"),
               _t("leve", energia="leve", prioridade="baixa")]
    r = escolher_agora(tarefas, hoje=HOJE, janela=15)
    assert [t.titulo for t in r] == ["leve"]


def test_janela_none_nao_filtra_nada():
    tarefas = [_t("pesada", energia="pesada", prioridade="alta"),
               _t("leve", energia="leve", prioridade="baixa")]
    r = escolher_agora(tarefas, hoje=HOJE, janela=None)
    assert len(r) == 2


def test_janela_ampla_mantem_tudo():
    tarefas = [_t("pesada", energia="pesada", prioridade="alta"),
               _t("leve", energia="leve", prioridade="baixa")]
    r = escolher_agora(tarefas, hoje=HOJE, janela=240)
    assert [t.titulo for t in r] == ["pesada", "leve"]


def test_nada_cabe_cai_para_ordem_normal_em_vez_de_tela_vazia():
    # princípio de design: nunca prender o usuário numa tela vazia
    tarefas = [_t("pesada", energia="pesada"), _t("outra", energia="pesada")]
    r = escolher_agora(tarefas, hoje=HOJE, janela=0)
    assert len(r) == 2


def test_mostra_menos_de_tres_se_so_uma_cabe():
    tarefas = [_t("leve", energia="leve"),
               _t("pesada 1", energia="pesada"),
               _t("pesada 2", energia="pesada"),
               _t("pesada 3", energia="pesada")]
    r = escolher_agora(tarefas, hoje=HOJE, janela=15)
    # "só sugere o que cabe": melhor uma opção honesta que três impossíveis
    assert [t.titulo for t in r] == ["leve"]


def test_janela_respeita_paginacao():
    tarefas = [_t(f"leve {i}", energia="leve") for i in range(5)]
    p0 = [t.titulo for t in escolher_agora(tarefas, hoje=HOJE, janela=60, offset=0)]
    p1 = [t.titulo for t in escolher_agora(tarefas, hoje=HOJE, janela=60, offset=3)]
    assert p0 != p1


def test_sem_janela_comportamento_da_fase_1_intacto():
    tarefas = [_t("baixa", prioridade="baixa"),
               _t("alta", prioridade="alta"),
               _t("media", prioridade="media")]
    r = escolher_agora(tarefas, hoje=HOJE)
    assert [t.titulo for t in r] == ["alta", "media", "baixa"]
