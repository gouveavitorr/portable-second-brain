import random
from app.pokemon import ClientePokeAPI, RAMOS_PREFERIDOS


def _no(nome, filhos=None):
    return {"species": {"name": nome}, "evolves_to": filhos or []}


def _dados(chain):
    return {
        "https://pokeapi.co/api/v2/pokemon/x": {
            "sprites": {"front_default": "https://img/x.png"},
            "species": {"url": "https://pokeapi.co/api/v2/pokemon-species/x"},
        },
        "https://pokeapi.co/api/v2/pokemon-species/x": {
            "evolution_chain": {"url": "https://pokeapi.co/api/v2/evolution-chain/1"},
        },
        "https://pokeapi.co/api/v2/evolution-chain/1": {"chain": chain},
    }


def _cliente(tmp_path, chain, chamadas=None):
    dados = _dados(chain)

    def fetch(url):
        if chamadas is not None:
            chamadas.append(url)
        return dados[url]
    return ClientePokeAPI(tmp_path, fetch=fetch)


def test_caminho_unico(tmp_path):
    chain = _no("charmander", [_no("charmeleon", [_no("charizard")])])
    c = _cliente(tmp_path, chain)
    assert c.cadeia_evolucao("x", random.Random(1)) == ["charmander", "charmeleon", "charizard"]


def test_especie_sem_evolucao(tmp_path):
    c = _cliente(tmp_path, _no("tauros"))
    assert c.cadeia_evolucao("x", random.Random(1)) == ["tauros"]


def test_ramo_preferido_gloom_vira_vileplume(tmp_path):
    chain = _no("oddish", [_no("gloom", [_no("vileplume"), _no("bellossom")])])
    c = _cliente(tmp_path, chain)
    for semente in range(5):
        assert c.cadeia_evolucao("x", random.Random(semente)) == ["oddish", "gloom", "vileplume"]


def test_ramo_preferido_eevee_vira_sylveon(tmp_path):
    ramos = [_no(n) for n in ["vaporeon", "jolteon", "flareon", "espeon",
                              "umbreon", "leafeon", "glaceon", "sylveon"]]
    c = _cliente(tmp_path, _no("eevee", ramos))
    for semente in range(5):
        assert c.cadeia_evolucao("x", random.Random(semente)) == ["eevee", "sylveon"]


def test_ramo_sem_preferencia_e_aleatorio(tmp_path):
    chain = _no("poliwag", [_no("poliwhirl", [_no("poliwrath"), _no("politoed")])])
    c = _cliente(tmp_path, chain)
    vistos = {c.cadeia_evolucao("x", random.Random(s))[-1] for s in range(30)}
    assert vistos == {"poliwrath", "politoed"}


def test_ramo_aleatorio_determinstico_por_semente(tmp_path):
    chain = _no("poliwag", [_no("poliwhirl", [_no("poliwrath"), _no("politoed")])])
    c = _cliente(tmp_path, chain)
    a = c.cadeia_evolucao("x", random.Random(7))
    b = c.cadeia_evolucao("x", random.Random(7))
    assert a == b


def test_ramos_preferidos_tem_as_duas_entradas():
    assert RAMOS_PREFERIDOS == {"gloom": "vileplume", "eevee": "sylveon"}


def test_sprite_ainda_funciona(tmp_path):
    c = _cliente(tmp_path, _no("x"))
    assert c.sprite("x") == "https://img/x.png"


def test_cache_evita_segunda_chamada(tmp_path):
    chamadas = []
    c = _cliente(tmp_path, _no("x"), chamadas)
    c.sprite("x")
    assert len(chamadas) > 0
    chamadas2 = []
    c2 = _cliente(tmp_path, _no("x"), chamadas2)
    c2.sprite("x")
    assert chamadas2 == []
