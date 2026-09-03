"""Gera o pool de cadeias da 1ª geração para dentro de second_brain/pokemons.md.

Ferramenta de manutenção: roda sob demanda, não faz parte do runtime do app.

    python -m scripts.gerar_pool
"""
from pathlib import Path

_BASE = "https://pokeapi.co/api/v2"


def _id_da_url(url: str) -> int:
    return int(url.rstrip("/").split("/")[-1])


def especies_gen1(fetch) -> list:
    dados = fetch(f"{_BASE}/generation/1")
    especies = dados["pokemon_species"]
    # a API devolve desordenado; o id da URL é a ordem da Pokédex
    especies = sorted(especies, key=lambda e: _id_da_url(e["url"]))
    return [e["name"] for e in especies]


def bases_com_evolucao(especies, fetch) -> list:
    bases = []
    vistas = set()
    for nome in especies:
        sp = fetch(f"{_BASE}/pokemon-species/{nome}")
        chain_url = sp.get("evolution_chain", {}).get("url")
        if not chain_url or chain_url in vistas:
            continue
        vistas.add(chain_url)
        chain = fetch(chain_url)["chain"]
        if not chain.get("evolves_to"):
            continue  # cadeia de membro único: sem evolução
        bases.append(chain["species"]["name"])
    return bases


def formatar_pokemons_md(bases) -> str:
    return "".join(f"- {b}\n" for b in bases)


def main() -> None:
    import json
    import re
    import httpx

    cache = Path("second_brain/.cache/pokeapi")
    cache.mkdir(parents=True, exist_ok=True)

    def fetch(url):
        arq = cache / (re.sub(r"[^a-zA-Z0-9]+", "_", url).strip("_") + ".json")
        if arq.exists():
            return json.loads(arq.read_text(encoding="utf-8"))
        resp = httpx.get(url, timeout=30.0)
        resp.raise_for_status()
        dados = resp.json()
        arq.write_text(json.dumps(dados), encoding="utf-8")
        return dados

    especies = especies_gen1(fetch)
    print(f"{len(especies)} espécies na gen 1")
    bases = bases_com_evolucao(especies, fetch)
    print(f"{len(bases)} cadeias com evolução")
    destino = Path("second_brain/pokemons.md")
    destino.write_text(formatar_pokemons_md(bases), encoding="utf-8")
    print(f"escrito em {destino}")


if __name__ == "__main__":
    main()
