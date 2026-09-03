"""Parser de `second_brain/dieta.md`.

Puro: nada aqui toca disco. Três leituras do mesmo arquivo:

- `parse_dieta` / `serializar_dieta` — round-trip pra escrita. Só as linhas de
  `## Compras` viram objeto (`Compra`); todo o resto volta como string intacta, então
  marcar um item comprado nunca reescreve a dieta.
- `refeicoes_de` — leitura estruturada e somente-leitura das refeições, pra tela.
- `corpo_de` — o comparativo antropométrico de `## Corpo`, também só leitura.
"""

import re
import secrets
from dataclasses import dataclass, field

_LINHA = re.compile(r"^- (.*)$")
_SECAO = re.compile(r"^##\s+(.*?)\s*$")
_GRUPO = re.compile(r"^###\s+(.*?)\s*$")
_SUB = re.compile(r"^####\s+(.*?)\s*$")
_OBS = re.compile(r"^>\s?(.*)$")
# "### 08:00 · Café da manhã"
_REFEICAO = re.compile(r"^###\s+(\d{2}:\d{2})\s*·\s*(.*?)\s*$")

_CAMPOS = {"qtd", "nota", "freq", "comprado", "id"}


@dataclass
class Compra:
    nome: str
    qtd: str | None = None
    nota: str | None = None
    freq: str | None = None       # 2x | semanal | quinzenal | mensal
    comprado: str | None = None   # AAAA-MM-DDTHH:MM de quando marquei
    id: str | None = None
    grupo: str | None = None      # título do `###` que abre o bloco (não serializa)


@dataclass
class ItemRefeicao:
    nome: str
    qtd: str | None = None
    kcal: str | None = None
    cat: str | None = None       # proteina | carbo | salada | fruta | liquido | molho


@dataclass
class Substituicao:
    titulo: str
    itens: list = field(default_factory=list)
    obs: str = ""


@dataclass
class Refeicao:
    hora: str
    nome: str
    itens: list = field(default_factory=list)
    obs: str = ""
    subs: list = field(default_factory=list)   # list[Substituicao], 0..n


@dataclass
class Medida:
    nome: str
    antes: str | None = None
    agora: str | None = None
    delta: str | None = None


@dataclass
class GrupoCorpo:
    titulo: str
    legenda: str = ""    # o que as colunas "antes" e "agora" significam neste grupo
    medidas: list = field(default_factory=list)


@dataclass
class Corpo:
    antes: str = ""      # data da avaliação anterior
    agora: str = ""      # data da avaliação mais recente
    grupos: list = field(default_factory=list)
    nota: str = ""       # observação livre sobre a avaliação


def gerar_id() -> str:
    return secrets.token_hex(2)


# O `.md` escreve a quantidade em duas linguagens ao mesmo tempo:
# "50 g (2 col. sopa cheias)", "2 unidades (100 g)", "1 caneca cheia (400 ml)".
# A medida caseira (colher, concha, pegador, xícara, caneca) é ruído na tela —
# some, some sempre em massa. `so_massa` devolve só o peso/volume.
_MASSA = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|mg|ml|g|l)(?![a-zà-ú])", re.IGNORECASE)


def so_massa(qtd: str | None) -> str | None:
    """`"2 unidades (100 g)"` -> `"100 g"`. Sem massa no texto, devolve como veio.

    O fallback é de propósito: na lista de compras existe "7 unidades" e
    "2 dúzias", que são como você compra, não medida caseira de porção.
    """
    if not qtd:
        return qtd
    m = _MASSA.search(qtd)
    if not m:
        return qtd
    return f"{m.group(1)} {m.group(2).lower()}"


def _campos_item(resto: str):
    partes = [p.strip() for p in resto.split("|")]
    dados = {}
    for seg in partes[1:]:
        chave, _, valor = seg.partition(":")
        dados[chave.strip()] = valor.strip()
    return partes[0], dados


# ---- round-trip (só as compras viram objeto) ----

def parse_dieta(texto: str) -> list:
    entradas: list = []
    em_compras = False
    grupo = None
    for linha in texto.splitlines():
        sec = _SECAO.match(linha)
        if sec and not linha.startswith("###"):
            em_compras = sec.group(1).strip().lower() == "compras"
            grupo = None
            entradas.append(linha)
            continue
        g = _GRUPO.match(linha)
        if g and not linha.startswith("####"):
            if em_compras:
                grupo = g.group(1)
            entradas.append(linha)
            continue
        m = _LINHA.match(linha)
        if not m or not em_compras:
            entradas.append(linha)
            continue
        nome, dados = _campos_item(m.group(1))
        c = Compra(nome=nome, grupo=grupo)
        for chave, valor in dados.items():
            if chave in _CAMPOS:
                setattr(c, chave, valor or None)
        entradas.append(c)
    return entradas


def serializar_linha(c: Compra) -> str:
    partes = [f"- {c.nome}"]
    for chave in ("qtd", "nota", "freq", "comprado", "id"):
        valor = getattr(c, chave)
        if valor:
            partes.append(f"{chave}:{valor}")
    return " | ".join(partes)


def serializar_dieta(entradas: list) -> str:
    linhas = [e if isinstance(e, str) else serializar_linha(e) for e in entradas]
    if not linhas:
        return ""
    return "\n".join(linhas) + "\n"


def garantir_ids(entradas: list) -> bool:
    mudou = False
    existentes = {e.id for e in entradas if isinstance(e, Compra) and e.id}
    for e in entradas:
        if not isinstance(e, Compra) or e.id:
            continue
        novo = gerar_id()
        while novo in existentes:
            novo = gerar_id()
        e.id = novo
        existentes.add(novo)
        mudou = True
    return mudou


# ---- leitura estruturada das refeições (somente leitura) ----

def refeicoes_de(texto: str) -> list:
    refeicoes: list = []
    atual = None
    sub = None          # substituição aberta, ou None quando estamos na opção principal
    em_refeicoes = False
    for linha in texto.splitlines():
        sec = _SECAO.match(linha)
        if sec and not linha.startswith("###"):
            em_refeicoes = sec.group(1).strip().lower() == "refeições"
            continue
        if not em_refeicoes:
            continue
        r = _REFEICAO.match(linha)
        if r:
            atual = Refeicao(hora=r.group(1), nome=r.group(2))
            refeicoes.append(atual)
            sub = None
            continue
        s = _SUB.match(linha)
        if s:
            sub = Substituicao(titulo=s.group(1))
            if atual is not None:
                atual.subs.append(sub)
            continue
        if atual is None:
            continue
        o = _OBS.match(linha)
        if o:
            alvo = sub if sub is not None else atual
            alvo.obs = (alvo.obs + " " + o.group(1)).strip()
            continue
        m = _LINHA.match(linha)
        if m:
            nome, dados = _campos_item(m.group(1))
            item = ItemRefeicao(nome=nome, qtd=dados.get("qtd"),
                                kcal=dados.get("kcal"), cat=dados.get("cat"))
            (sub.itens if sub is not None else atual.itens).append(item)
    return refeicoes


def itens_do_cardapio(refeicoes: list, incluir_subs: bool = False) -> list:
    """Os itens da opção principal do dia. Ignora `#### Substituição` por padrão.

    A lista de compras nasce daqui: você compra o que come todo dia, não o que
    talvez coma se trocar o almoço. Substituição usa o que já está na despensa.
    """
    itens = []
    for r in refeicoes:
        itens.extend(r.itens)
        if incluir_subs:
            for s in r.subs:
                itens.extend(s.itens)
    return itens


# "Maçã *ou* bergamota *ou* mamão + 1 col. de leite em pó" -> "Maçã"
# O primeiro nome é o que entra na lista; as alternativas são escolha do dia.
def ingrediente_base(nome: str) -> str:
    principal = nome.split("*ou*")[0]
    principal = principal.split("+")[0]
    principal = re.sub(r"\((?:cru[ao]?|crus|cozid[ao]|assad[ao]|ralad[ao])\)", "", principal)
    return principal.strip(" ,*")


# ---- comparativo antropométrico (somente leitura) ----

def corpo_de(texto: str) -> Corpo:
    corpo = Corpo()
    grupo = None
    em_corpo = False
    for linha in texto.splitlines():
        sec = _SECAO.match(linha)
        if sec and not linha.startswith("###"):
            em_corpo = sec.group(1).strip().lower() == "corpo"
            continue
        if not em_corpo:
            continue
        if linha.startswith("datas") and "|" in linha:
            _, dados = _campos_item(linha)
            corpo.antes = dados.get("antes", "")
            corpo.agora = dados.get("agora", "")
            continue
        g = _GRUPO.match(linha)
        if g and not linha.startswith("####"):
            grupo = GrupoCorpo(titulo=g.group(1))
            corpo.grupos.append(grupo)
            continue
        if linha.startswith("legenda:") and grupo is not None:
            grupo.legenda = linha.partition(":")[2].strip()
            continue
        o = _OBS.match(linha)
        if o:
            corpo.nota = (corpo.nota + " " + o.group(1)).strip()
            continue
        m = _LINHA.match(linha)
        if m and grupo is not None:
            nome, dados = _campos_item(m.group(1))
            grupo.medidas.append(Medida(nome=nome, antes=dados.get("antes"),
                                        agora=dados.get("agora"),
                                        delta=dados.get("delta")))
    return corpo
