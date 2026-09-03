from scripts.gerar_pool import (
    especies_gen1,
    bases_com_evolucao,
    formatar_pokemons_md,
)

_GEN1 = {
    "https://pokeapi.co/api/v2/generation/1": {
        "pokemon_species": [
            {"name": "pikachu", "url": "https://pokeapi.co/api/v2/pokemon-species/25/"},
            {"name": "bulbasaur", "url": "https://pokeapi.co/api/v2/pokemon-species/1/"},
            {"name": "ivysaur", "url": "https://pokeapi.co/api/v2/pokemon-species/2/"},
            {"name": "tauros", "url": "https://pokeapi.co/api/v2/pokemon-species/128/"},
        ]
    },
}

_SPECIES = {
    "bulbasaur": "c1", "ivysaur": "c1", "pikachu": "c2", "tauros": "c3",
}

_CHAINS = {
    "c1": {"chain": {"species": {"name": "bulbasaur"}, "evolves_to": [
        {"species": {"name": "ivysaur"}, "evolves_to": [
            {"species": {"name": "venusaur"}, "evolves_to": []}]}]}},
    "c2": {"chain": {"species": {"name": "pichu"}, "evolves_to": [
        {"species": {"name": "pikachu"}, "evolves_to": [
            {"species": {"name": "raichu"}, "evolves_to": []}]}]}},
    "c3": {"chain": {"species": {"name": "tauros"}, "evolves_to": []}},
}


def _fetch(url):
    if url in _GEN1:
        return _GEN1[url]
    for nome, chain_id in _SPECIES.items():
        if url == f"https://pokeapi.co/api/v2/pokemon-species/{nome}":
            return {"evolution_chain": {"url": f"https://pokeapi.co/api/v2/evolution-chain/{chain_id}"}}
    for chain_id, dados in _CHAINS.items():
        if url == f"https://pokeapi.co/api/v2/evolution-chain/{chain_id}":
            return dados
    raise KeyError(url)


def test_especies_gen1_ordenadas_por_id_da_pokedex():
    assert especies_gen1(_fetch) == ["bulbasaur", "ivysaur", "pikachu", "tauros"]


def test_bases_deduplica_por_cadeia():
    bases = bases_com_evolucao(["bulbasaur", "ivysaur"], _fetch)
    assert bases == ["bulbasaur"]


def test_bases_descarta_cadeia_de_membro_unico():
    assert bases_com_evolucao(["tauros"], _fetch) == []


def test_bases_usa_a_base_mesmo_de_outra_geracao():
    assert bases_com_evolucao(["pikachu"], _fetch) == ["pichu"]


def test_bases_preserva_ordem_de_entrada():
    bases = bases_com_evolucao(["bulbasaur", "pikachu", "tauros"], _fetch)
    assert bases == ["bulbasaur", "pichu"]


def test_formatar_pokemons_md():
    assert formatar_pokemons_md(["bulbasaur", "pichu"]) == "- bulbasaur\n- pichu\n"
