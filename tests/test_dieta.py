import random
from datetime import datetime

from fastapi.testclient import TestClient

from app.storage import Vault
from app.pokemon import ClientePokeAPI
from app.servico import Servico
from app.main import criar_app
from app.dieta import parse_dieta, serializar_dieta, refeicoes_de, corpo_de, Compra
from tests.test_api_diario import _fetch_fake

AGORA = datetime(2026, 7, 20, 10, 0)

DIETA = """# 🥗 Dieta

Prosa que deve sobreviver.

## Refeições

### 08:00 · Café da manhã
- Iogurte | qtd:100 g | kcal:45,2 | cat:liquido
- Mel | qtd:7 g | kcal:21,3 | cat:molho
> Misture tudo.

#### Substituição 1
- Pastel | qtd:30 g | kcal:86,0 | cat:carbo
> Air fryer por 10 min.

#### Substituição 2
- Maçã | qtd:150 g | kcal:78,0 | cat:fruta

### 12:00 · Almoço
- Alface | qtd:20 g | kcal:3,0 | cat:salada

## Compras

### Repor 2x por semana
- Iogurte | qtd:1,4 kg | nota:200 g/dia | freq:2x | id:k1

### Semanal
- Maçã | qtd:7 unidades | freq:semanal | id:k2

## Corpo

datas | antes:01/12/2025 | agora:18/07/2026

### Composição
legenda: dezembro → julho
- Peso | antes:102,10 kg | agora:106,70 kg | delta:+4,60
- Massa magra | antes:77,89 kg | agora:74,92 kg | delta:-2,97

> Medido de manhã, em jejum.
"""


def _servico(tmp_path):
    v = Vault(tmp_path)
    v.garantir()
    v.pokemons_md.write_text("- charmander\n", encoding="utf-8")
    v.dieta_md.write_text(DIETA, encoding="utf-8")
    s = Servico(v, ClientePokeAPI(v.cache_dir, fetch=_fetch_fake),
                rng=random.Random(1), agora=lambda: AGORA)
    return s, v


def _client(tmp_path):
    s, v = _servico(tmp_path)
    return TestClient(criar_app(s)), s, v


# --- parser: só as compras viram objeto ---

def test_so_compras_viram_objeto():
    compras = [e for e in parse_dieta(DIETA) if isinstance(e, Compra)]
    assert [c.nome for c in compras] == ["Iogurte", "Maçã"]


def test_compra_guarda_grupo_e_freq():
    compras = [e for e in parse_dieta(DIETA) if isinstance(e, Compra)]
    assert compras[0].grupo == "Repor 2x por semana"
    assert compras[0].freq == "2x" and compras[0].qtd == "1,4 kg"
    assert compras[1].grupo == "Semanal"


def test_itens_de_refeicao_nao_viram_compra():
    # as linhas "- Iogurte | qtd:100 g" das refeições continuam texto puro
    linhas = [e for e in parse_dieta(DIETA) if isinstance(e, str)]
    assert "- Iogurte | qtd:100 g | kcal:45,2 | cat:liquido" in linhas


def test_roundtrip_estavel():
    out = serializar_dieta(parse_dieta(DIETA))
    assert serializar_dieta(parse_dieta(out)) == out
    assert "Prosa que deve sobreviver" in out
    assert "### 08:00 · Café da manhã" in out


# --- leitura estruturada das refeições ---

def test_refeicoes_estruturadas():
    r = refeicoes_de(DIETA)
    assert [x.hora for x in r] == ["08:00", "12:00"]
    assert r[0].nome == "Café da manhã"
    assert [i.nome for i in r[0].itens] == ["Iogurte", "Mel"]
    assert r[0].itens[0].qtd == "100 g" and r[0].itens[0].kcal == "45,2"


def test_item_guarda_categoria():
    # a categoria é o que pinta o item na tela
    r = refeicoes_de(DIETA)
    assert [i.cat for i in r[0].itens] == ["liquido", "molho"]
    assert r[1].itens[0].cat == "salada"


def test_refeicao_separa_substituicoes_e_obs():
    r = refeicoes_de(DIETA)[0]
    assert r.obs == "Misture tudo."
    assert [s.titulo for s in r.subs] == ["Substituição 1", "Substituição 2"]
    assert [i.nome for i in r.subs[0].itens] == ["Pastel"]
    assert r.subs[0].obs == "Air fryer por 10 min."
    assert r.subs[1].itens[0].nome == "Maçã" and r.subs[1].obs == ""


def test_refeicao_sem_substituicao():
    assert refeicoes_de(DIETA)[1].subs == []


# --- comparativo antropométrico ---

def test_corpo_traz_datas_medidas_e_nota():
    c = corpo_de(DIETA)
    assert (c.antes, c.agora) == ("01/12/2025", "18/07/2026")
    assert [g.titulo for g in c.grupos] == ["Composição"]
    assert c.grupos[0].legenda == "dezembro → julho"
    m = c.grupos[0].medidas
    assert [x.nome for x in m] == ["Peso", "Massa magra"]
    assert (m[0].antes, m[0].agora, m[0].delta) == ("102,10 kg", "106,70 kg", "+4,60")
    assert c.nota == "Medido de manhã, em jejum."


def test_corpo_nao_pega_itens_das_refeicoes():
    # o parser do corpo só olha dentro de "## Corpo"
    nomes = [x.nome for g in corpo_de(DIETA).grupos for x in g.medidas]
    assert "Iogurte" not in nomes and "Alface" not in nomes


# --- serviço ---

def test_marcar_compra_grava_timestamp(tmp_path):
    s, _ = _servico(tmp_path)
    c = s.marcar_compra("k1", True)
    assert c.comprado == "2026-07-20T10:00"


def test_desmarcar_compra_limpa(tmp_path):
    s, _ = _servico(tmp_path)
    s.marcar_compra("k1", True)
    assert s.marcar_compra("k1", False).comprado is None


def test_marcar_compra_inexistente(tmp_path):
    s, _ = _servico(tmp_path)
    assert s.marcar_compra("zzz", True) is None


def test_marcar_compra_nao_mexe_no_resto(tmp_path):
    s, v = _servico(tmp_path)
    s.marcar_compra("k1", True)
    texto = v.dieta_md.read_text(encoding="utf-8")
    assert "- Iogurte | qtd:100 g | kcal:45,2 | cat:liquido" in texto   # refeição intacta
    assert "### 08:00 · Café da manhã" in texto
    assert "- Peso | antes:102,10 kg | agora:106,70 kg | delta:+4,60" in texto
    assert "comprado:2026-07-20T10:00" in texto


# --- API ---

def test_pagina_dieta_carrega(tmp_path):
    c, _, _ = _client(tmp_path)
    r = c.get("/dieta")
    assert r.status_code == 200 and "dieta.js" in r.text


def test_get_dieta_traz_refeicoes_e_compras(tmp_path):
    c, _, _ = _client(tmp_path)
    d = c.get("/api/dieta").json()
    assert [r["hora"] for r in d["refeicoes"]] == ["08:00", "12:00"]
    assert d["refeicoes"][0]["kcal"] == 66.5          # 45,2 + 21,3
    assert d["totais"]["kcal_dia"] == 69.5            # + 3,0 do almoço
    assert d["totais"]["itens"] == 2 and d["totais"]["comprados"] == 0


def test_get_dieta_traz_substituicoes_com_kcal(tmp_path):
    c, _, _ = _client(tmp_path)
    subs = c.get("/api/dieta").json()["refeicoes"][0]["subs"]
    assert [s["kcal"] for s in subs] == [86.0, 78.0]
    assert subs[0]["itens"][0]["cat"] == "carbo"


def test_get_dieta_traz_corpo(tmp_path):
    c, _, _ = _client(tmp_path)
    corpo = c.get("/api/dieta").json()["corpo"]
    assert corpo["agora"] == "18/07/2026"
    assert corpo["grupos"][0]["medidas"][1]["delta"] == "-2,97"
    assert "jejum" in corpo["nota"]


def test_patch_compra_marca_e_conta(tmp_path):
    c, _, _ = _client(tmp_path)
    r = c.patch("/api/dieta/compra/k1", json={"comprado": True})
    assert r.status_code == 200 and r.json()["comprado"] == "2026-07-20T10:00"
    assert c.get("/api/dieta").json()["totais"]["comprados"] == 1


def test_patch_compra_404(tmp_path):
    c, _, _ = _client(tmp_path)
    assert c.patch("/api/dieta/compra/zzz", json={"comprado": True}).status_code == 404
