"""Tarefas recorrentes: voltam sozinhas, nunca punem quem pulou um dia."""
from datetime import date
from app.tasks import Tarefa, parse_tarefas, serializar_linha
from app.engine import escolher_agora, disponivel, dias_para_voltar

HOJE = date(2026, 7, 14)


def _t(titulo, **kw):
    return Tarefa(titulo=titulo, **kw)


# --- parser ---

def test_parse_campos_repete_e_feito():
    (t,) = parse_tarefas("- [ ] Academia | repete:diario | feito:2026-07-13 | id:aa11")
    assert t.repete == "diario"
    assert t.feito == "2026-07-13"


def test_serializa_repete_e_feito():
    t = _t("Academia", repete="diario", feito="2026-07-13", id="aa11")
    assert serializar_linha(t) == "- [ ] Academia | repete:diario | feito:2026-07-13 | id:aa11"


def test_tarefa_normal_nao_ganha_campos():
    t = _t("X", id="aa11")
    assert serializar_linha(t) == "- [ ] X | id:aa11"


# --- disponibilidade ---

def test_nao_recorrente_sempre_disponivel():
    assert disponivel(_t("X"), HOJE) is True


def test_recorrente_nunca_feita_esta_disponivel():
    assert disponivel(_t("X", repete="diario"), HOJE) is True


def test_diaria_feita_hoje_some():
    assert disponivel(_t("X", repete="diario", feito="2026-07-14"), HOJE) is False


def test_diaria_feita_ontem_volta():
    assert disponivel(_t("X", repete="diario", feito="2026-07-13"), HOJE) is True


def test_semanal_feita_ha_3_dias_some():
    assert disponivel(_t("X", repete="semanal", feito="2026-07-11"), HOJE) is False


def test_semanal_feita_ha_8_dias_volta():
    assert disponivel(_t("X", repete="semanal", feito="2026-07-06"), HOJE) is True


def test_mensal_feita_ha_10_dias_some():
    assert disponivel(_t("X", repete="mensal", feito="2026-07-04"), HOJE) is False


def test_mensal_feita_ha_40_dias_volta():
    assert disponivel(_t("X", repete="mensal", feito="2026-06-04"), HOJE) is True


def test_pular_muitos_dias_nao_pune_so_volta():
    # princípio: sem punição. faltar 3 meses não gera nada além de estar disponível
    t = _t("Academia", repete="diario", feito="2026-04-01")
    assert disponivel(t, HOJE) is True


def test_feito_invalido_nao_quebra():
    assert disponivel(_t("X", repete="diario", feito="ontem"), HOJE) is True


def test_repete_desconhecido_trata_como_diario():
    assert disponivel(_t("X", repete="quinzenal", feito="2026-07-14"), HOJE) is False


# --- dias para voltar (estado da coluna de recorrentes) ---

def test_dias_para_voltar_zero_quando_disponivel():
    assert dias_para_voltar(_t("X", repete="semanal", feito="2026-07-06"), HOJE) == 0


def test_dias_para_voltar_zero_para_nao_recorrente():
    assert dias_para_voltar(_t("X"), HOJE) == 0


def test_dias_para_voltar_diaria_feita_hoje():
    assert dias_para_voltar(_t("X", repete="diario", feito="2026-07-14"), HOJE) == 1


def test_dias_para_voltar_semanal_feita_hoje():
    assert dias_para_voltar(_t("X", repete="semanal", feito="2026-07-14"), HOJE) == 7


def test_dias_para_voltar_semanal_feita_ha_3_dias():
    assert dias_para_voltar(_t("X", repete="semanal", feito="2026-07-11"), HOJE) == 4


def test_dias_para_voltar_feito_invalido_nao_quebra():
    assert dias_para_voltar(_t("X", repete="semanal", feito="ontem"), HOJE) == 0


# --- motor: recorrentes vivem na coluna, nunca no pool "Agora" ---

def test_motor_exclui_recorrente_pendente_do_pool():
    # recorrente pendente NÃO entra no "Escolha uma pra começar": tem coluna própria
    tarefas = [_t("Academia", repete="diario", feito="2026-07-13"),
               _t("Prateleira")]
    r = escolher_agora(tarefas, hoje=HOJE)
    assert [t.titulo for t in r] == ["Prateleira"]


def test_motor_exclui_recorrente_nunca_feita_do_pool():
    tarefas = [_t("Academia", repete="diario"), _t("Prateleira")]
    r = escolher_agora(tarefas, hoje=HOJE)
    assert [t.titulo for t in r] == ["Prateleira"]
