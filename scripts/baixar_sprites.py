"""Baixa e versiona os sprites do Pokémon pra o app rodar offline.

Ferramenta de **build**, não de runtime: roda uma vez, na sua máquina, COM internet.
Depois disso o app não precisa mais falar com a PokeAPI — os PNG ficam em
`static/pokemon/` e as cadeias de evolução (pré-resolvidas) em
`static/pokemon/cadeias.json`, tudo versionado no git.

    python -m scripts.baixar_sprites

O que ele cobre:
- todos os Pokémon do pool (`second_brain/pokemons.md`) e **todas** as evoluções deles,
  em todos os ramos (o ramo é sorteado em runtime, então cada possibilidade precisa do
  sprite);
- os Pokémon de meta do financeiro (a reserva e qualquer meta fixa).

Rode de novo se o pool ou as metas mudarem.
"""
import json
from pathlib import Path

from app.pokemon import ClientePokeAPI, especies_da_arvore
from app.financeiro import META_RESERVA, METAS_FIXAS

RAIZ = Path(__file__).resolve().parent.parent
POOL_MD = RAIZ / "second_brain" / "pokemons.md"
CACHE = RAIZ / "second_brain" / ".cache" / "pokeapi"
DESTINO = RAIZ / "static" / "pokemon"


def ler_pool(caminho: Path) -> list:
    slugs = []
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha.startswith("- "):
            slugs.append(linha[2:].strip())
    return slugs


def slugs_de_meta() -> list:
    return [META_RESERVA["pokemon"], *(m["pokemon"] for m in METAS_FIXAS)]


def baixar_png(url: str) -> bytes:
    import httpx
    resp = httpx.get(url, timeout=30.0)
    resp.raise_for_status()
    return resp.content


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    cliente = ClientePokeAPI(CACHE)   # sem sprites_dir/cadeias: modo build (rede)

    pool = ler_pool(POOL_MD)
    metas = slugs_de_meta()
    print(f"pool: {len(pool)} bases · metas: {metas}")

    cadeias: dict = {}
    especies: set = set(metas)

    for slug in pool:
        arvore = cliente.arvore_evolucao(slug)
        if arvore is None:
            especies.add(slug)
            continue
        cadeias[slug] = arvore
        especies.update(especies_da_arvore(arvore))

    print(f"{len(especies)} sprites a garantir ({len(cadeias)} cadeias resolvidas)")

    baixados, pulados = 0, []
    for slug in sorted(especies):
        arq = DESTINO / f"{slug}.png"
        if arq.exists():
            continue
        url = cliente.sprite(slug)   # rede: devolve a URL do front_default
        if not url:
            pulados.append(slug)
            continue
        arq.write_bytes(baixar_png(url))
        baixados += 1

    (DESTINO / "cadeias.json").write_text(
        json.dumps(cadeias, ensure_ascii=False), encoding="utf-8")

    print(f"baixados {baixados} sprite(s) novos em {DESTINO.relative_to(RAIZ)}")
    print(f"cadeias em {(DESTINO / 'cadeias.json').relative_to(RAIZ)}")
    if pulados:
        print(f"sem sprite (pulados): {pulados}")


if __name__ == "__main__":
    main()
