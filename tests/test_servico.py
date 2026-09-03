import json
import random
from app.storage import Vault
from app.pokemon import ClientePokeAPI
from app.servico import Servico

_ARVORES = {
    "char": {"species": {"name": "charmander"}, "evolves_to": [
        {"species": {"name": "charmeleon"}, "evolves_to": [
            {"species": {"name": "charizard"}, "evolves_to": []}]}]},
    "pika": {"species": {"name": "pichu"}, "evolves_to": [
        {"species": {"name": "pikachu"}, "evolves_to": [
            {"species": {"name": "raichu"}, "evolves_to": []}]}]},
}

# como na PokeAPI real: qualquer membro da cadeia aponta para a mesma evolution-chain
_ESPECIE_CADEIA = {
    "charmander": "char", "charmeleon": "char", "charizard": "char",
    "pichu": "pika", "pikachu": "pika", "raichu": "pika",
}

_PREFIXO = "https://pokeapi.co/api/v2"


def _fetch_fake(url):
    for nome, chave in _ESPECIE_CADEIA.items():
        if url == f"{_PREFIXO}/pokemon/{nome}":
            return {"sprites": {"front_default": f"https://img/{nome}.png"},
                    "species": {"url": f"{_PREFIXO}/pokemon-species/{nome}"}}
        if url == f"{_PREFIXO}/pokemon-species/{nome}":
            return {"evolution_chain": {"url": f"{_PREFIXO}/evolution-chain/{chave}"}}
    for chave, arvore in _ARVORES.items():
        if url == f"{_PREFIXO}/evolution-chain/{chave}":
            return {"chain": arvore}
    raise KeyError(url)


def _servico(tmp_path, pool="- charmander\n", semente=1):
    v = Vault(tmp_path)
    v.garantir()
    v.pokemons_md.write_text(pool, encoding="utf-8")
    cliente = ClientePokeAPI(v.cache_dir, fetch=_fetch_fake)
    return Servico(v, cliente, rng=random.Random(semente)), v


def test_adicionar_e_listar(tmp_path):
    s, v = _servico(tmp_path)
    s.adicionar_tarefa({"titulo": "fazer X", "prioridade": "alta"})
    tarefas = s.listar_tarefas()
    assert len(tarefas) == 1
    assert tarefas[0].titulo == "fazer X"
    assert tarefas[0].id is not None


def test_editar_marca_concluida_e_da_xp(tmp_path):
    s, v = _servico(tmp_path)
    t = s.adicionar_tarefa({"titulo": "pesada", "energia": "pesada"})
    antes = s.estado_pokemon()["xp"]
    s.editar_tarefa(t.id, {"concluida": True})
    assert s.estado_pokemon()["xp"] == antes + 25


def test_concluir_duas_vezes_nao_da_xp_dobrado(tmp_path):
    s, v = _servico(tmp_path)
    t = s.adicionar_tarefa({"titulo": "leve", "energia": "leve"})
    s.editar_tarefa(t.id, {"concluida": True})
    xp1 = s.estado_pokemon()["xp"]
    s.editar_tarefa(t.id, {"concluida": True})
    assert s.estado_pokemon()["xp"] == xp1


def test_primeiro_run_pega_o_primeiro_do_pool_e_grava_cadeia(tmp_path):
    # o primeiro companheiro é fixo: o topo de pokemons.md. nada de sorteio aqui.
    s, v = _servico(tmp_path, pool="- charmander\n- pichu\n")
    est = s.estado_pokemon()
    assert est["nome"] == "Charmander"
    d = json.loads(v.progresso_json.read_text(encoding="utf-8"))
    assert d["cadeia"] == ["charmander", "charmeleon", "charizard"]


def test_primeiro_run_e_igual_com_qualquer_semente(tmp_path):
    import random as _r
    nomes = set()
    for semente in range(5):
        sub = tmp_path / f"v{semente}"
        sub.mkdir()
        s, v = _servico(sub, pool="- charmander\n- pichu\n", semente=semente)
        nomes.add(s.estado_pokemon()["nome"])
    assert nomes == {"Charmander"}


def test_pokemon_persiste_entre_aberturas(tmp_path):
    s, v = _servico(tmp_path, pool="- charmander\n- pichu\n")
    primeiro = s.estado_pokemon()["nome"]
    for _ in range(3):
        cliente = ClientePokeAPI(v.cache_dir, fetch=_fetch_fake)
        outro = Servico(v, cliente, rng=random.Random(99))
        assert outro.estado_pokemon()["nome"] == primeiro


def test_estado_pokemon_usa_cadeia_gravada(tmp_path):
    s, v = _servico(tmp_path, pool="- charmander\n")
    est = s.estado_pokemon()
    assert est["nome"] == "Charmander"
    assert est["sprite"] == "https://img/charmander.png"
    assert est["xp"] == 0
    assert est["xp_para_evoluir"] == 100
    assert est["estagio"] == 0


def test_migracao_progresso_sem_cadeia(tmp_path):
    s, v = _servico(tmp_path, pool="- charmander\n")
    # arquivo no formato antigo, sem o campo "cadeia"
    v.progresso_json.write_text(json.dumps({
        "pokemon_atual": "charmeleon", "xp": 40, "concluidos": [],
    }), encoding="utf-8")
    est = s.estado_pokemon()
    assert est["nome"] == "Charmeleon"
    assert est["estagio"] == 1
    d = json.loads(v.progresso_json.read_text(encoding="utf-8"))
    assert d["cadeia"] == ["charmander", "charmeleon", "charizard"]


def test_persistencia_entre_instancias(tmp_path):
    s, v = _servico(tmp_path)
    s.adicionar_tarefa({"titulo": "persistir"})
    cliente = ClientePokeAPI(v.cache_dir, fetch=_fetch_fake)
    s2 = Servico(v, cliente, rng=random.Random(1))
    assert [t.titulo for t in s2.listar_tarefas()] == ["persistir"]
