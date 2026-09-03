import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# Custo de cada evolução, por estágio da cadeia: a primeira é barata, as
# seguintes pesam mais. Estágio além do terceiro repete o último valor.
LIMIARES_XP = (100, 200, 300)
LIMIAR_XP = LIMIARES_XP[0]

_XP = {"leve": 10, "pesada": 25}


def xp_por_energia(energia):
    return _XP.get(energia or "media", 15)


def limiar_do_estagio(estagio):
    idx = min(max(estagio, 0), len(LIMIARES_XP) - 1)
    return LIMIARES_XP[idx]


# A PokeAPI devolve slug (`nidoran-m`, `mr-mime`); a tela mostra o nome de gente.
NOMES_ESPECIAIS = {
    "nidoran-m": "Nidoran♂",
    "nidoran-f": "Nidoran♀",
    "mr-mime": "Mr. Mime",
    "mr-rime": "Mr. Rime",
    "mime-jr": "Mime Jr.",
    "farfetchd": "Farfetch'd",
    "sirfetchd": "Sirfetch'd",
    "ho-oh": "Ho-Oh",
    "porygon-z": "Porygon-Z",
    "type-null": "Type: Null",
    "jangmo-o": "Jangmo-o",
    "hakamo-o": "Hakamo-o",
    "kommo-o": "Kommo-o",
}


def nome_bonito(especie):
    slug = (especie or "").strip().lower()
    if not slug:
        return ""
    if slug in NOMES_ESPECIAIS:
        return NOMES_ESPECIAIS[slug]
    return " ".join(parte.capitalize() for parte in slug.split("-") if parte)


@dataclass
class Progresso:
    pokemon_atual: str
    xp: int = 0
    concluidos: list = field(default_factory=list)
    cadeia: list = field(default_factory=list)


def sortear_proximo(favoritos, concluidos, rng):
    candidatos = [p for p in favoritos if p not in concluidos]
    if candidatos:
        return rng.choice(candidatos), list(concluidos)
    # todos concluídos: sorteia entre todos e limpa
    return rng.choice(favoritos), []


def aplicar_xp(prog, ganho, pool, resolver_cadeia, rng):
    ganho = max(0, ganho)
    xp = prog.xp + ganho
    atual = prog.pokemon_atual
    cadeia = list(prog.cadeia) or [atual]
    concluidos = list(prog.concluidos)

    while True:
        try:
            idx = cadeia.index(atual)
        except ValueError:
            idx = len(cadeia) - 1  # trata como estágio final
        limiar = limiar_do_estagio(idx)
        if xp < limiar:
            break
        if idx < len(cadeia) - 1:
            atual = cadeia[idx + 1]
            xp -= limiar
        else:
            xp -= limiar
            if atual not in concluidos:
                concluidos.append(atual)
            atual, concluidos = sortear_proximo(pool, concluidos, rng)
            cadeia = resolver_cadeia(atual)
            # novo companheiro: para aqui e deixa o excedente para ele
            break

    return Progresso(pokemon_atual=atual, xp=xp,
                     concluidos=concluidos, cadeia=cadeia)


# --- Cliente PokeAPI com cache em disco ---

_BASE = "https://pokeapi.co/api/v2"

# Ramos escolhidos pelo usuário quando a cadeia se divide.
RAMOS_PREFERIDOS = {"gloom": "vileplume", "eevee": "sylveon"}


def _slug_url(url: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", url).strip("_")


def _fetch_httpx(url: str) -> dict:
    import httpx
    resp = httpx.get(url, timeout=15.0)
    resp.raise_for_status()
    return resp.json()


class ClientePokeAPI:
    def __init__(self, cache_dir, fetch=None):
        self.cache_dir = Path(cache_dir)
        self._fetch = fetch or _fetch_httpx

    def _get(self, url: str) -> dict:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        arq = self.cache_dir / (_slug_url(url) + ".json")
        if arq.exists():
            return json.loads(arq.read_text(encoding="utf-8"))
        dados = self._fetch(url)
        arq.write_text(json.dumps(dados), encoding="utf-8")
        return dados

    def sprite(self, especie: str):
        dados = self._get(f"{_BASE}/pokemon/{especie}")
        return dados.get("sprites", {}).get("front_default")

    def cadeia_evolucao(self, especie: str, rng):
        p = self._get(f"{_BASE}/pokemon/{especie}")
        species_url = p.get("species", {}).get("url")
        if not species_url:
            return [especie]
        sp = self._get(species_url)
        chain_url = sp.get("evolution_chain", {}).get("url")
        if not chain_url:
            return [especie]
        arvore = self._get(chain_url).get("chain")
        return self._achatar_cadeia(arvore, rng)

    @staticmethod
    def _escolher_ramo(nome_atual, filhos, rng):
        preferido = RAMOS_PREFERIDOS.get(nome_atual)
        if preferido:
            for f in filhos:
                if f["species"]["name"] == preferido:
                    return f
        if len(filhos) == 1:
            return filhos[0]
        return rng.choice(filhos)

    @classmethod
    def _achatar_cadeia(cls, no, rng) -> list:
        nomes = []
        atual = no
        while atual:
            nome = atual["species"]["name"]
            nomes.append(nome)
            filhos = atual.get("evolves_to") or []
            atual = cls._escolher_ramo(nome, filhos, rng) if filhos else None
        return nomes
