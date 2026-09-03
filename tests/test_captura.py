"""Captura rápida: inbox da tela Agora e inbox da dieta.

As duas escrevem direto no vault sem passar por confirmação — o ponto é o
atrito zero. O que se testa aqui é que a linha cai no lugar certo e que o
resto do arquivo sobrevive intacto.
"""

import random
from datetime import datetime

from fastapi.testclient import TestClient

from app.storage import Vault
from app.pokemon import ClientePokeAPI
from app.servico import Servico
from app.main import criar_app
from tests.test_api_diario import _fetch_fake

AGORA = datetime(2026, 7, 23, 10, 0)

INBOX = """# 📥 Inbox

Prosa de instrução que não conta como item.

## Pra triar

<!-- escreve abaixo desta linha -->
"""

DIETA = """# 🥗 Dieta

Prosa que deve sobreviver.

## Refeições

### 08:00 · Café da manhã
- Iogurte | qtd:100 g | kcal:45,2 | cat:liquido

## Compras

### Semanal
- Iogurte | qtd:1 pote | freq:semanal | id:aaaa
"""


def _servico(tmp_path, inbox=INBOX, dieta=DIETA):
    v = Vault(tmp_path)
    v.garantir()
    v.pokemons_md.write_text("- charmander\n", encoding="utf-8")
    v.inbox_md.write_text(inbox, encoding="utf-8")
    v.dieta_md.write_text(dieta, encoding="utf-8")
    return Servico(v, ClientePokeAPI(v.cache_dir, fetch=_fetch_fake),
                   rng=random.Random(1), agora=lambda: AGORA)


# ---- inbox da tela Agora ----

def test_despejar_inbox_acrescenta_linha(tmp_path):
    s = _servico(tmp_path)
    r = s.despejar_inbox("comprar pão")
    assert r["pendentes"] == 1
    texto = s.vault.inbox_md.read_text(encoding="utf-8")
    assert "- comprar pão" in texto
    assert "Prosa de instrução" in texto  # o cabeçalho sobreviveu


def test_despejar_inbox_empilha_sem_perder_o_anterior(tmp_path):
    s = _servico(tmp_path)
    s.despejar_inbox("primeiro")
    s.despejar_inbox("segundo")
    assert s.listar_inbox() == ["primeiro", "segundo"]
    assert s.contar_inbox() == 2


def test_despejar_inbox_vazio_recusa(tmp_path):
    s = _servico(tmp_path)
    for entrada in ("", "   ", None):
        try:
            s.despejar_inbox(entrada)
        except ValueError:
            continue
        raise AssertionError(f"aceitou {entrada!r}")


def test_api_captura_rapida(tmp_path):
    s = _servico(tmp_path)
    c = TestClient(criar_app(s))
    r = c.post("/api/inbox", json={"texto": "ideia solta"})
    assert r.status_code == 201
    assert r.json()["pendentes"] == 1
    assert c.get("/api/inbox").json()["pendentes"] == 1
    assert c.post("/api/inbox", json={"texto": "  "}).status_code == 400


# ---- inbox da dieta ----

def test_despejar_dieta_cria_secao_no_topo(tmp_path):
    s = _servico(tmp_path)
    s.despejar_dieta("comprei o nhoque")
    texto = s.vault.dieta_md.read_text(encoding="utf-8")
    assert "## Inbox da dieta" in texto
    # entra antes das Refeições, não no fim do arquivo
    assert texto.index("## Inbox da dieta") < texto.index("## Refeições")
    assert "2026-07-23 · comprei o nhoque" in texto


def test_despejar_dieta_nao_quebra_as_compras(tmp_path):
    s = _servico(tmp_path)
    s.despejar_dieta("será que troco o kibe?")
    d = s.listar_dieta()
    assert [c.nome for c in d["compras"]] == ["Iogurte"]
    assert d["compras"][0].id == "aaaa"
    assert len(d["refeicoes"]) == 1


def test_notas_da_dieta_mais_recente_primeiro(tmp_path):
    s = _servico(tmp_path)
    s.despejar_dieta("primeira")
    s.despejar_dieta("segunda")
    notas = s.listar_notas_dieta()
    assert notas[0].endswith("segunda")
    assert notas[1].endswith("primeira")


def test_api_inbox_dieta(tmp_path):
    s = _servico(tmp_path)
    c = TestClient(criar_app(s))
    r = c.post("/api/dieta/inbox", json={"texto": "comprei tomate"})
    assert r.status_code == 201
    assert any("comprei tomate" in n for n in r.json()["notas"])
    assert c.get("/api/dieta").json()["notas"]
    assert c.post("/api/dieta/inbox", json={"texto": ""}).status_code == 400
