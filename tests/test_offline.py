"""Cobre o modo offline (Fase 2) e a resolução/semeadura do vault (Fase 3)."""
import random

import pytest

from app import storage
from app.pokemon import ClientePokeAPI, especies_da_arvore


# --- sprites offline ---

def test_sprite_local_quando_png_existe(tmp_path):
    sd = tmp_path / "pokemon"
    sd.mkdir()
    (sd / "pikachu.png").write_bytes(b"png")
    c = ClientePokeAPI(tmp_path, sprites_dir=sd)
    assert c.sprite("Pikachu") == "/static/pokemon/pikachu.png"


def test_sprite_cai_na_rede_quando_png_falta(tmp_path):
    sd = tmp_path / "pokemon"
    sd.mkdir()
    chamou = []

    def fetch(url):
        chamou.append(url)
        return {"sprites": {"front_default": "http://img/x.png"}}

    c = ClientePokeAPI(tmp_path, fetch=fetch, sprites_dir=sd)
    assert c.sprite("x") == "http://img/x.png"
    assert chamou  # sem PNG local, bateu na rede


# --- cadeias offline ---

_ARVORE_BULBA = {
    "species": {"name": "bulbasaur"},
    "evolves_to": [{
        "species": {"name": "ivysaur"},
        "evolves_to": [{"species": {"name": "venusaur"}, "evolves_to": []}],
    }],
}


def test_cadeia_offline_nao_bate_na_rede(tmp_path):
    def fetch(url):
        raise AssertionError(f"não deveria chamar a rede: {url}")

    c = ClientePokeAPI(tmp_path, fetch=fetch, cadeias={"bulbasaur": _ARVORE_BULBA})
    assert c.cadeia_evolucao("bulbasaur", random.Random(1)) == [
        "bulbasaur", "ivysaur", "venusaur"]


def test_especies_da_arvore_pega_todos_os_ramos():
    arvore = {
        "species": {"name": "eevee"},
        "evolves_to": [
            {"species": {"name": "vaporeon"}, "evolves_to": []},
            {"species": {"name": "jolteon"}, "evolves_to": []},
        ],
    }
    assert set(especies_da_arvore(arvore)) == {"eevee", "vaporeon", "jolteon"}


# --- vault: caminho + semeadura ---

def test_caminho_do_vault_respeita_env(monkeypatch, tmp_path):
    monkeypatch.setenv("SECOND_BRAIN_VAULT", str(tmp_path / "x"))
    assert storage.caminho_do_vault() == tmp_path / "x"


def test_preparar_vault_semeia_quando_nao_existe(tmp_path, monkeypatch):
    semente = tmp_path / "semente"
    semente.mkdir()
    (semente / "tarefas.md").write_text("# t\n", encoding="utf-8")
    (semente / "progresso.json").write_text("{}", encoding="utf-8")  # deve ser ignorado
    destino = tmp_path / "vault"  # ainda não existe
    monkeypatch.setenv("SECOND_BRAIN_VAULT", str(destino))
    monkeypatch.setattr(storage, "_dir_semente", lambda: semente)

    v = storage.preparar_vault()
    assert v.base == destino
    assert (destino / "tarefas.md").exists()
    # o que é estado do usuário (progresso.json) não vem na semente
    assert not (destino / "progresso.json").exists()


def test_preparar_vault_semeia_pasta_vazia(tmp_path, monkeypatch):
    # a pasta pode já existir (criada por um log/marcador) sem o conteúdo do vault;
    # ainda assim precisa da semente — o gatilho é "falta tarefas.md", não "não existe"
    destino = tmp_path / "vault"
    destino.mkdir()
    (destino / ".servidor.log").write_text("ruido\n", encoding="utf-8")  # não é vault
    semente = tmp_path / "semente"
    semente.mkdir()
    (semente / "tarefas.md").write_text("# t\n", encoding="utf-8")
    monkeypatch.setenv("SECOND_BRAIN_VAULT", str(destino))
    monkeypatch.setattr(storage, "_dir_semente", lambda: semente)

    storage.preparar_vault()
    assert (destino / "tarefas.md").exists()          # semeou mesmo com a pasta existindo
    assert (destino / ".servidor.log").exists()       # e não apagou o que já estava lá


def test_preparar_vault_nao_sobrescreve_o_que_ja_existe(tmp_path, monkeypatch):
    destino = tmp_path / "vault"
    destino.mkdir()
    (destino / "tarefas.md").write_text("meu\n", encoding="utf-8")
    semente = tmp_path / "semente"
    semente.mkdir()
    (semente / "tarefas.md").write_text("semente\n", encoding="utf-8")
    monkeypatch.setenv("SECOND_BRAIN_VAULT", str(destino))
    monkeypatch.setattr(storage, "_dir_semente", lambda: semente)

    storage.preparar_vault()
    assert (destino / "tarefas.md").read_text(encoding="utf-8") == "meu\n"
