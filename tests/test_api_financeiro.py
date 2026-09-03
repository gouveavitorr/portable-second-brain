import random
from datetime import datetime
from fastapi.testclient import TestClient
from app.storage import Vault
from app.pokemon import ClientePokeAPI
from app.servico import Servico
from app.main import criar_app
from tests.test_api_diario import _fetch_fake

FIN = """# Financeiro

## Recebimentos
- Ana | valor:450 | id:a1
- Bia | valor:240 | id:a2
- Contrato pausado | valor:0 | pausado:sim | id:a3

## Fixos
- Aluguel | valor:1900 | id:f1
- Luz | valor:140 | id:f2

## Contas
- Aluguel | parcela:1/2 | valor:1900 | faltante:1900 | id:c1
- Luz | parcela:1/2 | valor:140 | faltante:0 | id:c2

## Gastos
- Padaria | data:2026-06-04 | valor:56 | id:g1

## Mês
- guardado | valor:69
"""


def _client(tmp_path, agora=datetime(2026, 7, 20, 10, 0)):
    v = Vault(tmp_path)
    v.garantir()
    v.pokemons_md.write_text("- charmander\n", encoding="utf-8")
    v.financeiro_md.write_text(FIN, encoding="utf-8")
    s = Servico(v, ClientePokeAPI(v.cache_dir, fetch=_fetch_fake),
                rng=random.Random(1), agora=lambda: agora)
    return TestClient(criar_app(s)), s


def test_pagina_financeiro_carrega(tmp_path):
    c, _ = _client(tmp_path)
    r = c.get("/financeiro")
    assert r.status_code == 200
    assert "financeiro.js" in r.text


def test_get_financeiro_totais(tmp_path):
    c, _ = _client(tmp_path)
    d = c.get("/api/financeiro").json()
    assert len(d["recebimentos"]) == 3
    t = d["totais"]
    assert t["ativos"] == 2                 # o contrato pausado fica de fora
    assert t["esperado"] == 690             # 450 + 240
    assert t["recebido"] == 0
    assert t["pagos"] == 0
    assert t["contas_total"] == 2040        # 1900 + 140
    # nenhuma marcada como paga ainda: as duas parcelas do mês estão em aberto
    assert t["contas_a_pagar"] == 2040
    # faltante é saldo de parcelas FUTURAS: a luz está na última (0), o aluguel tem +1
    assert t["contas_faltante"] == 1900


def test_get_financeiro_custo_fixo_e_guardado(tmp_path):
    c, _ = _client(tmp_path)
    t = c.get("/api/financeiro").json()["totais"]
    assert t["custo_fixo"] == 2040          # só os Fixos, não as parcelas
    assert t["renda"] == 690                # igual ao esperado: pausada fora
    assert t["guardado"] == 69
    assert t["meta_guardado"] == 14280      # 2040 × 7 meses de reserva
    assert t["falta_guardar"] == 14211


def test_get_financeiro_lista_fixos(tmp_path):
    c, _ = _client(tmp_path)
    fixos = c.get("/api/financeiro").json()["fixos"]
    assert [f["nome"] for f in fixos] == ["Aluguel", "Luz"]
    assert fixos[0]["valor"] == 1900.0 and fixos[0]["pago"] is None


def test_patch_fixo_pago(tmp_path):
    c, _ = _client(tmp_path)
    r = c.patch("/api/financeiro/fixo/f1", json={"pago": True})
    assert r.status_code == 200 and r.json()["pago"] == "2026-07-20T10:00"


def test_patch_fixo_inexistente_404(tmp_path):
    c, _ = _client(tmp_path)
    assert c.patch("/api/financeiro/fixo/zzzz", json={"pago": True}).status_code == 404


def test_patch_mes_grava_guardado(tmp_path):
    c, _ = _client(tmp_path)
    r = c.patch("/api/financeiro/mes", json={"guardado": 7140})
    assert r.status_code == 200
    assert r.json()["guardado"] == 7140 and r.json()["pct_guardado"] == 50
    assert c.get("/api/financeiro").json()["totais"]["guardado"] == 7140


def test_patch_mes_sem_numero_400(tmp_path):
    c, _ = _client(tmp_path)
    assert c.patch("/api/financeiro/mes", json={"guardado": "muito"}).status_code == 400


def test_get_financeiro_numeros_viram_float(tmp_path):
    c, _ = _client(tmp_path)
    ana = next(e for e in c.get("/api/financeiro").json()["recebimentos"] if e["nome"] == "Ana")
    assert ana["valor"] == 450.0 and ana["pausado"] is False


def test_patch_entrada_recebida_reflete_no_recebido(tmp_path):
    c, _ = _client(tmp_path)
    r = c.patch("/api/financeiro/entrada/a1", json={"pago": True})
    assert r.status_code == 200
    assert r.json()["pago"] == "2026-07-20T10:00"
    assert c.get("/api/financeiro").json()["totais"]["recebido"] == 450


def test_patch_entrada_inexistente_404(tmp_path):
    c, _ = _client(tmp_path)
    assert c.patch("/api/financeiro/entrada/zzzz", json={"pago": True}).status_code == 404


def test_patch_conta_paga(tmp_path):
    c, _ = _client(tmp_path)
    r = c.patch("/api/financeiro/conta/c1", json={"pago": True})
    assert r.status_code == 200 and r.json()["pago"] == "2026-07-20T10:00"


def test_pagar_conta_reduz_a_pagar_mas_nao_o_faltante(tmp_path):
    # marcar como paga tira do "a pagar" do mês; o saldo de parcelas futuras não muda
    c, _ = _client(tmp_path)
    c.patch("/api/financeiro/conta/c1", json={"pago": True})
    t = c.get("/api/financeiro").json()["totais"]
    assert t["contas_a_pagar"] == 140
    assert t["contas_faltante"] == 1900


def test_post_gasto_cria_e_lista(tmp_path):
    c, _ = _client(tmp_path)
    r = c.post("/api/financeiro/gasto", json={"local": "Mercado", "valor": 30})
    assert r.status_code == 201
    assert r.json()["local"] == "Mercado" and r.json()["data"] == "2026-07-20"
    locais = [g["local"] for g in c.get("/api/financeiro").json()["gastos"]]
    assert "Mercado" in locais


def test_post_gasto_sem_local_400(tmp_path):
    c, _ = _client(tmp_path)
    assert c.post("/api/financeiro/gasto", json={"valor": 10}).status_code == 400
