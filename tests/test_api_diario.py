import random
from datetime import datetime
from fastapi.testclient import TestClient
from app.storage import Vault
from app.pokemon import ClientePokeAPI
from app.servico import Servico
from app.main import criar_app

_PREFIXO = "https://pokeapi.co/api/v2"


def _fetch_fake(url):
    dados = {
        f"{_PREFIXO}/pokemon/charmander": {
            "sprites": {"front_default": "https://img/charmander.png"},
            "species": {"url": f"{_PREFIXO}/pokemon-species/charmander"},
        },
        f"{_PREFIXO}/pokemon-species/charmander": {
            "evolution_chain": {"url": f"{_PREFIXO}/evolution-chain/2"},
        },
        f"{_PREFIXO}/evolution-chain/2": {
            "chain": {"species": {"name": "charmander"}, "evolves_to": []},
        },
    }
    return dados[url]


def _client(tmp_path, agora=datetime(2026, 7, 15, 14, 32)):
    v = Vault(tmp_path)
    v.garantir()
    v.pokemons_md.write_text("- charmander\n", encoding="utf-8")
    s = Servico(v, ClientePokeAPI(v.cache_dir, fetch=_fetch_fake),
                rng=random.Random(1), agora=lambda: agora)
    return TestClient(criar_app(s)), s


def test_post_diario_cria_anotacao(tmp_path):
    c, _ = _client(tmp_path)
    r = c.post("/api/diario", json={"texto": "arrumei a cozinha", "energia": "pesada"})
    assert r.status_code == 201
    assert r.json() == {"dia": "2026-07-15", "hora": "14:32",
                        "texto": "arrumei a cozinha", "energia": "pesada"}


def test_post_diario_sem_energia_vira_media(tmp_path):
    c, _ = _client(tmp_path)
    r = c.post("/api/diario", json={"texto": "fiz uma coisa"})
    assert r.status_code == 201
    assert r.json()["energia"] == "média"


def test_post_diario_texto_vazio_da_400(tmp_path):
    c, _ = _client(tmp_path)
    assert c.post("/api/diario", json={"texto": "   "}).status_code == 400
    assert c.post("/api/diario", json={}).status_code == 400


def test_post_diario_da_xp(tmp_path):
    c, _ = _client(tmp_path)
    c.post("/api/diario", json={"texto": "caminhada", "energia": "pesada"})
    assert c.get("/api/pokemon").json()["xp"] == 25


def test_get_diario_traz_hoje_por_padrao(tmp_path):
    c, s = _client(tmp_path)
    c.post("/api/diario", json={"texto": "de ontem", "energia": "leve"})
    s._agora = lambda: datetime(2026, 7, 16, 9, 0)
    c.post("/api/diario", json={"texto": "de hoje", "energia": "leve"})

    assert [a["texto"] for a in c.get("/api/diario").json()["anotacoes"]] == ["de hoje"]


def test_get_diario_por_dia_e_tudo(tmp_path):
    c, s = _client(tmp_path)
    c.post("/api/diario", json={"texto": "de ontem", "energia": "leve"})
    s._agora = lambda: datetime(2026, 7, 16, 9, 0)
    c.post("/api/diario", json={"texto": "de hoje", "energia": "leve"})

    r = c.get("/api/diario?dia=2026-07-15").json()["anotacoes"]
    assert [a["texto"] for a in r] == ["de ontem"]
    r = c.get("/api/diario?dia=tudo").json()["anotacoes"]
    assert [a["texto"] for a in r] == ["de hoje", "de ontem"]
