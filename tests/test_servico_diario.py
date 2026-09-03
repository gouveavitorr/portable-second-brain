import random
from datetime import datetime
import pytest
from app.storage import Vault
from app.pokemon import ClientePokeAPI
from app.servico import Servico

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


def _servico(tmp_path, agora=datetime(2026, 7, 15, 14, 32)):
    v = Vault(tmp_path)
    v.garantir()
    v.pokemons_md.write_text("- charmander\n", encoding="utf-8")
    s = Servico(v, ClientePokeAPI(v.cache_dir, fetch=_fetch_fake),
                rng=random.Random(1), agora=lambda: agora)
    return s, v


def test_anotar_grava_com_o_horario_do_relogio(tmp_path):
    s, v = _servico(tmp_path)
    a = s.anotar("arrumei a cozinha", "pesada")
    assert (a.dia, a.hora, a.texto, a.energia) == \
        ("2026-07-15", "14:32", "arrumei a cozinha", "pesada")
    assert v.diario_md.read_text(encoding="utf-8") == (
        "# 📓 Diário\n\n## 2026-07-15\n\n- 14:32 — arrumei a cozinha (pesada)\n"
    )


def test_anotar_sem_energia_vira_media(tmp_path):
    s, _ = _servico(tmp_path)
    assert s.anotar("fiz uma coisa", None).energia == "média"


def test_energia_sem_acento_e_normalizada(tmp_path):
    s, _ = _servico(tmp_path)
    assert s.anotar("fiz uma coisa", "media").energia == "média"


def test_energia_desconhecida_vira_media(tmp_path):
    s, _ = _servico(tmp_path)
    assert s.anotar("fiz uma coisa", "gigante").energia == "média"


def test_anotar_da_xp_da_energia_escolhida(tmp_path):
    s, _ = _servico(tmp_path)
    s.anotar("caminhada longa", "pesada")
    assert s.estado_pokemon()["xp"] == 25
    s.anotar("lavei a louça", "leve")
    assert s.estado_pokemon()["xp"] == 35
    s.anotar("respondi emails", None)
    assert s.estado_pokemon()["xp"] == 50  # média = 15


def test_texto_vazio_nao_grava_nem_da_xp(tmp_path):
    s, v = _servico(tmp_path)
    with pytest.raises(ValueError):
        s.anotar("   ", "leve")
    assert not v.diario_md.exists()
    assert s.estado_pokemon()["xp"] == 0


def test_quebra_de_linha_no_texto_vira_uma_anotacao_so(tmp_path):
    s, v = _servico(tmp_path)
    s.anotar("arrumei\na cozinha", "leve")
    assert v.diario_md.read_text(encoding="utf-8").count("- 14:32") == 1
    assert "arrumei a cozinha" in v.diario_md.read_text(encoding="utf-8")


def test_listar_anotacoes_filtra_por_dia(tmp_path):
    s, v = _servico(tmp_path)
    s.anotar("de ontem", "leve")
    s._agora = lambda: datetime(2026, 7, 16, 9, 0)
    s.anotar("de hoje", "leve")

    assert [a.texto for a in s.listar_anotacoes()] == ["de hoje"]
    assert [a.texto for a in s.listar_anotacoes("2026-07-15")] == ["de ontem"]
    assert [a.texto for a in s.listar_anotacoes("tudo")] == ["de hoje", "de ontem"]


def test_anotacoes_do_mesmo_dia_saem_mais_recente_primeiro(tmp_path):
    s, _ = _servico(tmp_path)
    s.anotar("primeira", "leve")
    s._agora = lambda: datetime(2026, 7, 15, 18, 0)
    s.anotar("segunda", "leve")
    assert [a.texto for a in s.listar_anotacoes()] == ["segunda", "primeira"]
