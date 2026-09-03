import random
from fastapi.testclient import TestClient
from app.storage import Vault
from app.pokemon import ClientePokeAPI
from app.servico import Servico
from app.main import criar_app


def _fetch_fake(url):
    dados = {
        "https://pokeapi.co/api/v2/pokemon/charmander": {
            "sprites": {"front_default": "https://img/charmander.png"},
            "species": {"url": "https://pokeapi.co/api/v2/pokemon-species/charmander"},
        },
        "https://pokeapi.co/api/v2/pokemon-species/charmander": {
            "evolution_chain": {"url": "https://pokeapi.co/api/v2/evolution-chain/2"},
        },
        "https://pokeapi.co/api/v2/evolution-chain/2": {
            "chain": {"species": {"name": "charmander"}, "evolves_to": []},
        },
    }
    return dados[url]


def _client(tmp_path):
    v = Vault(tmp_path)
    v.garantir()
    v.pokemons_md.write_text("- charmander\n", encoding="utf-8")
    servico = Servico(v, ClientePokeAPI(v.cache_dir, fetch=_fetch_fake), rng=random.Random(1))
    return TestClient(criar_app(servico))


def test_post_e_get_tarefas(tmp_path):
    c = _client(tmp_path)
    r = c.post("/api/tarefas", json={"titulo": "fazer X", "prioridade": "alta"})
    assert r.status_code == 201
    assert r.json()["titulo"] == "fazer X"
    r2 = c.get("/api/tarefas")
    assert len(r2.json()["tarefas"]) == 1


def test_patch_conclui(tmp_path):
    c = _client(tmp_path)
    tid = c.post("/api/tarefas", json={"titulo": "X", "energia": "leve"}).json()["id"]
    r = c.patch(f"/api/tarefas/{tid}", json={"concluida": True})
    assert r.status_code == 200
    assert r.json()["concluida"] is True
    assert c.get("/api/pokemon").json()["xp"] == 10


def test_patch_id_inexistente_404(tmp_path):
    c = _client(tmp_path)
    assert c.patch("/api/tarefas/zzzz", json={"concluida": True}).status_code == 404


def test_agora_devolve_no_maximo_3(tmp_path):
    c = _client(tmp_path)
    for i in range(5):
        c.post("/api/tarefas", json={"titulo": f"t{i}"})
    r = c.get("/api/agora")
    assert len(r.json()["tarefas"]) == 3


def test_pokemon_endpoint(tmp_path):
    c = _client(tmp_path)
    est = c.get("/api/pokemon").json()
    assert est["nome"] == "Charmander"
    assert est["xp_para_evoluir"] == 100
