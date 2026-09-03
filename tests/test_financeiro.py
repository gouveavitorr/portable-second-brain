import random
from datetime import datetime

import pytest

from app.storage import Vault
from app.pokemon import ClientePokeAPI
from app.servico import Servico
from app.financeiro import (
    parse_financeiro, serializar_financeiro, serializar_linha, resumo,
    Entrada, Conta, Fixo, Gasto, Mes,
)
from tests.test_servico import _fetch_fake

AGORA = datetime(2026, 7, 20, 10, 0)

FIN = """# 💰 Financeiro

texto de prosa que deve sobreviver ao round-trip.

## Recebimentos
- Ana | valor:450 | id:a1
- Contrato pausado | valor:0 | pausado:sim | id:a2

## Fixos
- Aluguel | valor:1900 | id:f1
- Luz | valor:140 | pago:2026-07-01 | id:f2

## Contas
- Aluguel | parcela:1/2 | valor:1900 | faltante:1900 | id:c1

## Gastos
- Padaria | data:2026-06-04 | valor:56 | id:g1

## Mês
- guardado | valor:90
"""


def _servico(tmp_path):
    v = Vault(tmp_path)
    v.garantir()
    v.pokemons_md.write_text("- charmander\n", encoding="utf-8")
    v.financeiro_md.write_text(FIN, encoding="utf-8")
    s = Servico(v, ClientePokeAPI(v.cache_dir, fetch=_fetch_fake),
                rng=random.Random(1), agora=lambda: AGORA)
    return s, v


# --- parser ---

def test_parse_classifica_por_secao():
    tipos = [type(x).__name__ for x in parse_financeiro(FIN) if not isinstance(x, str)]
    assert tipos == ["Entrada", "Entrada", "Fixo", "Fixo", "Conta", "Gasto", "Mes"]


def test_parse_fixo_nao_tem_parcela():
    aluguel = [x for x in parse_financeiro(FIN) if isinstance(x, Fixo)][0]
    assert aluguel.nome == "Aluguel" and aluguel.valor == "1900" and aluguel.pago is None


def test_serializa_fixo():
    f = Fixo(nome="Luz", valor="140", pago="2026-07-01", id="f2")
    assert serializar_linha(f) == "- Luz | valor:140 | pago:2026-07-01 | id:f2"


def test_parse_mes_aceita_sem_acento():
    entradas = parse_financeiro("## Mes\n- guardado | valor:1500\n")
    assert [x.valor for x in entradas if isinstance(x, Mes)] == ["1500"]


def test_parse_pausado():
    pausada = [x for x in parse_financeiro(FIN)
               if isinstance(x, Entrada) and x.nome == "Contrato pausado"][0]
    assert pausada.pausado is True


def test_parse_valor_fica_string_crua():
    ana = [x for x in parse_financeiro(FIN)
           if isinstance(x, Entrada) and x.nome == "Ana"][0]
    assert ana.valor == "450"


def test_roundtrip_preserva_prosa_e_campos():
    out = serializar_financeiro(parse_financeiro(FIN))
    assert serializar_financeiro(parse_financeiro(out)) == out  # estável
    assert "## Recebimentos" in out
    assert "prosa que deve sobreviver" in out
    assert "pausado:sim" in out


def test_serializa_entrada():
    e = Entrada(nome="Ana", valor="450", id="a1")
    assert serializar_linha(e) == "- Ana | valor:450 | id:a1"


# --- resumo (custo fixo, renda, guardado) ---

def test_resumo_soma_fixos_e_ignora_contas():
    # 1900 + 140 dos Fixos; o Aluguel repetido em Contas não entra
    assert resumo(parse_financeiro(FIN))["custo_fixo"] == 2040


def test_resumo_renda_ignora_pausado():
    assert resumo(parse_financeiro(FIN))["renda"] == 450


def test_resumo_meta_e_sete_meses_de_custo_fixo():
    r = resumo(parse_financeiro(FIN))
    assert r["meta_guardado"] == 14280        # 2040 × 7
    assert r["falta_guardar"] == 14190        # meta − 90 guardados


def test_resumo_percentual_e_sobre_a_meta():
    r = resumo(parse_financeiro(FIN))
    assert r["guardado"] == 90 and r["pct_guardado"] == 1   # 90 / 14280


def test_resumo_percentual_nao_passa_de_100():
    md = "## Fixos\n- Luz | valor:100 | id:f1\n## Mês\n- guardado | valor:99999\n"
    r = resumo(parse_financeiro(md))
    assert r["pct_guardado"] == 100 and r["falta_guardar"] == 0


def test_resumo_sem_as_secoes_novas_e_zero():
    r = resumo(parse_financeiro("## Recebimentos\n- Ana | valor:450 | id:a1\n"))
    assert r["custo_fixo"] == 0 and r["guardado"] == 0 and r["pct_guardado"] == 0


def test_resumo_sem_custo_fixo_nao_divide():
    r = resumo(parse_financeiro("## Mês\n- guardado | valor:100\n"))
    assert r["meta_guardado"] == 0 and r["pct_guardado"] == 0


def test_resumo_valor_vazio_conta_zero():
    r = resumo(parse_financeiro("## Fixos\n- Luz | id:f1\n- Água | valor:50 | id:f2\n"))
    assert r["custo_fixo"] == 50


def test_serializa_gasto_usa_local():
    g = Gasto(local="Padaria", data="2026-06-04", valor="56", id="g1")
    assert serializar_linha(g) == "- Padaria | data:2026-06-04 | valor:56 | id:g1"


# --- serviço ---

def test_marcar_entrada_recebida_grava_timestamp(tmp_path):
    s, _ = _servico(tmp_path)
    e = s.editar_entrada("a1", {"pago": True})
    assert e.pago == "2026-07-20T10:00"


def test_desmarcar_entrada_limpa_campo(tmp_path):
    s, _ = _servico(tmp_path)
    s.editar_entrada("a1", {"pago": True})
    e = s.editar_entrada("a1", {"pago": False})
    assert e.pago is None


def test_marcar_conta_paga_grava_timestamp(tmp_path):
    s, _ = _servico(tmp_path)
    c = s.editar_conta("c1", {"pago": True})
    assert c.pago == "2026-07-20T10:00"


def test_marcar_fixo_pago_grava_timestamp(tmp_path):
    s, _ = _servico(tmp_path)
    f = s.editar_fixo("f1", {"pago": True})
    assert f.pago == "2026-07-20T10:00"


def test_definir_guardado_sobrescreve(tmp_path):
    s, v = _servico(tmp_path)
    s.definir_guardado(200.0)
    assert s.listar_financeiro()["resumo"]["guardado"] == 200
    # o .md é lido por humano: sem o `.0` pendurado
    assert "- guardado | valor:200" in v.financeiro_md.read_text(encoding="utf-8")


def test_definir_guardado_cria_secao_quando_falta(tmp_path):
    v = Vault(tmp_path)
    v.garantir()
    v.pokemons_md.write_text("- charmander\n", encoding="utf-8")
    v.financeiro_md.write_text("## Recebimentos\n- Ana | valor:450 | id:a1\n", encoding="utf-8")
    s = Servico(v, ClientePokeAPI(v.cache_dir, fetch=_fetch_fake), agora=lambda: AGORA)
    s.definir_guardado(45)
    assert "## Mês" in v.financeiro_md.read_text(encoding="utf-8")
    assert s.listar_financeiro()["resumo"]["guardado"] == 45


def test_editar_entrada_inexistente_retorna_none(tmp_path):
    s, _ = _servico(tmp_path)
    assert s.editar_entrada("zzzz", {"pago": True}) is None


def test_adicionar_gasto_data_de_hoje_e_persiste(tmp_path):
    s, _ = _servico(tmp_path)
    g = s.adicionar_gasto({"local": "Mercado", "valor": 30})
    assert g.local == "Mercado" and g.data == "2026-07-20" and g.valor == "30" and g.id
    gastos = s.listar_financeiro()["gastos"]
    assert [x.local for x in gastos if x.local == "Mercado"] == ["Mercado"]


def test_adicionar_gasto_entra_no_topo_da_secao(tmp_path):
    s, _ = _servico(tmp_path)
    s.adicionar_gasto({"local": "Mercado", "valor": 30})
    gastos = s.listar_financeiro()["gastos"]
    assert gastos[0].local == "Mercado"   # mais recente no topo


def test_adicionar_gasto_sem_local_erro(tmp_path):
    s, _ = _servico(tmp_path)
    with pytest.raises(ValueError):
        s.adicionar_gasto({"valor": 10})


def test_ids_gerados_quando_faltam(tmp_path):
    v = Vault(tmp_path)
    v.garantir()
    v.pokemons_md.write_text("- charmander\n", encoding="utf-8")
    v.financeiro_md.write_text("## Recebimentos\n- SemId | valor:100\n", encoding="utf-8")
    s = Servico(v, ClientePokeAPI(v.cache_dir, fetch=_fetch_fake), agora=lambda: AGORA)
    recebimentos = s.listar_financeiro()["recebimentos"]
    assert recebimentos[0].id  # atribuído no primeiro load
