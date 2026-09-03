import random
from datetime import datetime

from fastapi.testclient import TestClient

from app.storage import Vault
from app.pokemon import ClientePokeAPI
from app.servico import Servico
from app.main import criar_app
from app.objetivos import (
    parse_objetivos, indexar_tarefas, montar, slug, nome_projeto,
)
from app.tasks import parse_tarefas, serializar_tarefas, Tarefa
from tests.test_servico import _fetch_fake

OBJ = """# 🎯 Objetivos

## Aprender violão

Direção de longo prazo. Projeto principal: [[projetos/curso-violao]]. Também
empurram [[projetos/comprar-instrumento]] e [[projetos/curso-violao]] (repetido).

## Ter uma reserva

A caixinha da reserva em [[tarefas]] começou a empurrar.

## Correr uma maratona

Ainda sem nada empurrando.

## Nota

Isto não é um objetivo e não deve virar card.
"""

TAR = """# ✅ Tarefas

## Recorrentes
- [ ] Beber água | repete:diario | id:r1

## Curso de violão
- [ ] Achar um professor | id:t1
- [ ] Marcar a primeira aula | id:t2

## Comprar instrumento
- [ ] Pesquisar preços | id:t3

## Reserva
- [x] Abrir a caixinha | feito:2026-08-09 | id:t4
- [ ] Depositar este mês | objetivo:ter-uma-reserva | id:t5
"""


def test_slug_e_nome_projeto():
    assert slug("Aprender violão") == "aprender-violao"
    assert slug("Correr uma maratona") == "correr-uma-maratona"
    assert nome_projeto("curso-violao") == "Curso Violao"
    assert nome_projeto("comprar-instrumento") == "Comprar Instrumento"


def test_parse_pula_nota_e_pega_projetos():
    objs = parse_objetivos(OBJ)
    titulos = [o.titulo for o in objs]
    assert "Nota" not in titulos
    assert titulos == ["Aprender violão", "Ter uma reserva", "Correr uma maratona"]
    violao = next(o for o in objs if o.slug == "aprender-violao")
    # dedup: curso-violao aparece duas vezes no texto, entra uma
    assert violao.projetos == ["curso-violao", "comprar-instrumento"]
    reserva = next(o for o in objs if o.slug == "ter-uma-reserva")
    assert reserva.projetos == []  # não linka projeto


def test_indexar_conta_so_ativas_e_le_tag():
    por_secao, por_objetivo = indexar_tarefas(TAR)
    # recorrente ativa conta na sua seção
    assert por_secao["recorrentes"] == 1
    assert por_secao["curso-de-violao"] == 2
    assert por_secao["comprar-instrumento"] == 1
    # concluída não conta; a ativa com tag sim
    assert por_secao["reserva"] == 1
    assert por_objetivo == {"ter-uma-reserva": 1}


def test_montar_cruza_projeto_e_tag():
    dados = {o["slug"]: o for o in montar(OBJ, TAR)}

    # violão: 2 tasks da seção "Curso de violão" + 1 de "Comprar instrumento"
    # (casamento por subconjunto, apesar do "de" no cabeçalho)
    violao = dados["aprender-violao"]
    assert violao["em_andamento"] == 3
    assert [p["nome"] for p in violao["projetos"]] == ["Curso Violao",
                                                       "Comprar Instrumento"]

    # reserva: sem projeto, mas a task solta com objetivo:ter-uma-reserva empurra
    reserva = dados["ter-uma-reserva"]
    assert reserva["em_andamento"] == 1
    assert reserva["projetos"] == []

    # maratona: nada empurrando — o alerta de objetivo parado
    assert dados["correr-uma-maratona"]["em_andamento"] == 0


def test_round_trip_preserva_objetivo():
    linha = "- [ ] X | objetivo:ter-uma-reserva | id:z1"
    t = [e for e in parse_tarefas(linha) if isinstance(e, Tarefa)][0]
    assert t.objetivo == "ter-uma-reserva"
    assert "objetivo:ter-uma-reserva" in serializar_tarefas([t])


def _client(tmp_path):
    v = Vault(tmp_path)
    v.garantir()
    v.pokemons_md.write_text("- charmander\n", encoding="utf-8")
    v.objetivos_md.write_text(OBJ, encoding="utf-8")
    v.tarefas_md.write_text(TAR, encoding="utf-8")
    s = Servico(v, ClientePokeAPI(v.cache_dir, fetch=_fetch_fake),
                rng=random.Random(1), agora=lambda: datetime(2026, 8, 9, 10, 0))
    return TestClient(criar_app(s))


def test_pagina_objetivos_carrega(tmp_path):
    c = _client(tmp_path)
    assert c.get("/objetivos").status_code == 200


def test_api_objetivos(tmp_path):
    c = _client(tmp_path)
    r = c.get("/api/objetivos")
    assert r.status_code == 200
    objs = r.json()["objetivos"]
    assert [o["titulo"] for o in objs] == [
        "Aprender violão", "Ter uma reserva", "Correr uma maratona"]
    violao = next(o for o in objs if o["slug"] == "aprender-violao")
    assert violao["em_andamento"] == 3
