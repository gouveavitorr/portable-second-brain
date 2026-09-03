import random
from datetime import datetime
from app.storage import Vault
from app.pokemon import ClientePokeAPI
from app.servico import Servico
from tests.test_servico import _fetch_fake

AGORA = datetime(2026, 7, 14, 10, 0)


def _servico(tmp_path):
    v = Vault(tmp_path)
    v.garantir()
    v.pokemons_md.write_text("- charmander\n", encoding="utf-8")
    s = Servico(v, ClientePokeAPI(v.cache_dir, fetch=_fetch_fake),
                rng=random.Random(1), agora=lambda: AGORA)
    return s, v


def test_concluir_recorrente_registra_feito_e_nao_marca_x(tmp_path):
    s, v = _servico(tmp_path)
    t = s.adicionar_tarefa({"titulo": "Academia", "repete": "diario"})
    s.editar_tarefa(t.id, {"concluida": True})
    (nova,) = [x for x in s.listar_tarefas() if x.id == t.id]
    assert nova.concluida is False          # não morre pra sempre
    assert nova.feito == "2026-07-14"       # mas registra que saiu hoje


def test_concluir_recorrente_ainda_da_xp(tmp_path):
    s, v = _servico(tmp_path)
    t = s.adicionar_tarefa({"titulo": "Academia", "repete": "diario",
                            "energia": "pesada"})
    antes = s.estado_pokemon()["xp"]
    s.editar_tarefa(t.id, {"concluida": True})
    assert s.estado_pokemon()["xp"] == antes + 25


def test_concluir_recorrente_duas_vezes_no_mesmo_dia_nao_dobra_xp(tmp_path):
    s, v = _servico(tmp_path)
    t = s.adicionar_tarefa({"titulo": "Academia", "repete": "diario"})
    s.editar_tarefa(t.id, {"concluida": True})
    xp1 = s.estado_pokemon()["xp"]
    s.editar_tarefa(t.id, {"concluida": True})
    assert s.estado_pokemon()["xp"] == xp1


def test_recorrente_some_do_agora_apos_concluida(tmp_path):
    s, v = _servico(tmp_path)
    t = s.adicionar_tarefa({"titulo": "Academia", "repete": "diario"})
    s.adicionar_tarefa({"titulo": "Prateleira"})
    s.editar_tarefa(t.id, {"concluida": True})
    from app.engine import escolher_agora
    titulos = [x.titulo for x in escolher_agora(s.listar_tarefas(), hoje=s.hoje())]
    assert titulos == ["Prateleira"]


def test_tarefa_normal_continua_marcando_x(tmp_path):
    s, v = _servico(tmp_path)
    t = s.adicionar_tarefa({"titulo": "Prateleira"})
    s.editar_tarefa(t.id, {"concluida": True})
    (nova,) = [x for x in s.listar_tarefas() if x.id == t.id]
    assert nova.concluida is True
    assert nova.feito is None


# --- timestamp: concluir vira entrada no diário "Acabei de fazer" ---

def test_concluir_recorrente_registra_no_diario(tmp_path):
    s, v = _servico(tmp_path)
    t = s.adicionar_tarefa({"titulo": "Academia", "repete": "diario",
                            "energia": "pesada"})
    s.editar_tarefa(t.id, {"concluida": True})
    anotacoes = s.listar_anotacoes()
    assert [(a.hora, a.texto, a.energia) for a in anotacoes] == [
        ("10:00", "Academia", "pesada")]


def test_concluir_normal_registra_no_diario(tmp_path):
    s, v = _servico(tmp_path)
    t = s.adicionar_tarefa({"titulo": "Prateleira"})
    s.editar_tarefa(t.id, {"concluida": True})
    assert [a.texto for a in s.listar_anotacoes()] == ["Prateleira"]


def test_concluir_duas_vezes_no_mesmo_dia_nao_dobra_diario(tmp_path):
    s, v = _servico(tmp_path)
    t = s.adicionar_tarefa({"titulo": "Academia", "repete": "diario"})
    s.editar_tarefa(t.id, {"concluida": True})
    s.editar_tarefa(t.id, {"concluida": True})
    assert len(s.listar_anotacoes()) == 1


def test_editar_recorrente_sem_concluir_nao_registra_diario(tmp_path):
    s, v = _servico(tmp_path)
    t = s.adicionar_tarefa({"titulo": "Academia", "repete": "diario"})
    s.editar_tarefa(t.id, {"passo": "vestir a roupa"})
    assert s.listar_anotacoes() == []
