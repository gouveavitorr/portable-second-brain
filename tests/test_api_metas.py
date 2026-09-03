import random
from datetime import datetime
from fastapi.testclient import TestClient
from app.storage import Vault
from app.pokemon import ClientePokeAPI
from app.servico import Servico
from app.main import criar_app

FIN = """# Financeiro

## Recebimentos
- Ana | valor:450 | id:a1

## Fixos
- Aluguel | valor:1900 | id:f1
- Luz | valor:140 | id:f2

## Mês
- guardado | valor:69
"""


def _fetch_fake(url):
    dados = {
        "https://pokeapi.co/api/v2/pokemon/togepi": {
            "sprites": {"front_default": "https://img/togepi.png"},
        },
    }
    return dados[url]


def _client(tmp_path, agora=datetime(2026, 8, 9, 10, 0)):
    v = Vault(tmp_path)
    v.garantir()
    v.pokemons_md.write_text("- charmander\n", encoding="utf-8")
    v.financeiro_md.write_text(FIN, encoding="utf-8")
    s = Servico(v, ClientePokeAPI(v.cache_dir, fetch=_fetch_fake),
                rng=random.Random(1), agora=lambda: agora)
    return TestClient(criar_app(s)), s


def test_get_metas_so_a_reserva_de_fabrica(tmp_path):
    c, _ = _client(tmp_path)
    metas = c.get("/api/metas").json()["metas"]
    assert [m["chave"] for m in metas] == ["reserva"]

    reserva = metas[0]
    # reserva tem meta dinâmica: custo fixo (1900+140) × 7
    assert reserva["pokemon"] == "togepi"
    assert reserva["sprite"] == "https://img/togepi.png"
    assert reserva["nome"] == "Togepi"
    assert reserva["guardado"] == 69 and reserva["meta"] == 14280


def test_patch_meta_reserva_grava_e_reflete_no_financeiro(tmp_path):
    # reserva grava na mesma linha `- guardado`: o Financeiro enxerga a mudança
    c, _ = _client(tmp_path)
    r = c.patch("/api/metas/reserva", json={"valor": 7140})
    assert r.status_code == 200
    reserva = next(m for m in r.json()["metas"] if m["chave"] == "reserva")
    assert reserva["guardado"] == 7140 and reserva["pct"] == 50   # 7140 / 14280
    assert c.get("/api/financeiro").json()["totais"]["guardado"] == 7140


def test_patch_meta_reserva_virgula_decimal(tmp_path):
    c, _ = _client(tmp_path)
    r = c.patch("/api/metas/reserva", json={"valor": "1500,50"})
    reserva = next(m for m in r.json()["metas"] if m["chave"] == "reserva")
    assert reserva["guardado"] == 1500.5


def test_deposito_reserva_soma_ao_guardado(tmp_path):
    # o número digitado é uma quantia depositada: soma, não substitui
    c, _ = _client(tmp_path)
    r = c.post("/api/metas/reserva/deposito", json={"valor": 31})
    assert r.status_code == 200
    reserva = next(m for m in r.json()["metas"] if m["chave"] == "reserva")
    assert reserva["guardado"] == 100     # 69 + 31
    assert c.get("/api/financeiro").json()["totais"]["guardado"] == 100
    # outro depósito continua somando
    r2 = c.post("/api/metas/reserva/deposito", json={"valor": 500})
    reserva2 = next(m for m in r2.json()["metas"] if m["chave"] == "reserva")
    assert reserva2["guardado"] == 600


def test_deposito_virgula_decimal(tmp_path):
    c, _ = _client(tmp_path)
    r = c.post("/api/metas/reserva/deposito", json={"valor": "0,50"})
    reserva = next(m for m in r.json()["metas"] if m["chave"] == "reserva")
    assert reserva["guardado"] == 69.5


def test_deposito_negativo_ou_zero_400(tmp_path):
    c, _ = _client(tmp_path)
    assert c.post("/api/metas/reserva/deposito", json={"valor": -100}).status_code == 400
    assert c.post("/api/metas/reserva/deposito", json={"valor": 0}).status_code == 400


def test_deposito_sem_numero_400(tmp_path):
    c, _ = _client(tmp_path)
    assert c.post("/api/metas/reserva/deposito", json={"valor": "muito"}).status_code == 400


def test_deposito_meta_desconhecida_404(tmp_path):
    c, _ = _client(tmp_path)
    assert c.post("/api/metas/marte/deposito", json={"valor": 100}).status_code == 404


def test_patch_meta_desconhecida_404(tmp_path):
    c, _ = _client(tmp_path)
    assert c.patch("/api/metas/marte", json={"valor": 100}).status_code == 404


def test_patch_meta_sem_numero_400(tmp_path):
    c, _ = _client(tmp_path)
    assert c.patch("/api/metas/reserva", json={"valor": "muito"}).status_code == 400
