"""Leitura de `objetivos.md` e o cruzamento com o que está em andamento.

A tela Objetivos responde uma pergunta só: *o que está fazendo cada objetivo de
longo prazo andar agora?* Isso são os projetos que o objetivo linka (`[[projetos/x]]`)
e as tarefas ativas nas seções desses projetos — mais tarefas soltas que apontem
direto pro objetivo via `objetivo:<slug>`. Objetivo sem nada em andamento aparece
parado, que é o alerta útil (a própria nota do `objetivos.md` fala disso).

Tudo aqui é leitura pura: a tela não edita objetivo (objetivo não é tarefa, não tem
botão de "feito").
"""

import re
import unicodedata
from dataclasses import dataclass, field

from app.tasks import parse_tarefas, Tarefa

_LINK_PROJETO = re.compile(r"\[\[projetos/([a-z0-9-]+)\]\]")
_CABECALHO = re.compile(r"^##\s+(.*?)\s*$")

# seções de `objetivos.md` que não são objetivos
_NAO_OBJETIVO = {"nota"}

# palavras que ficam minúsculas no meio do nome do projeto, e siglas que sobem
_MINUSCULAS = {"na", "no", "de", "do", "da", "dos", "das", "e"}
# siglas que devem aparecer em maiúsculas no chip da tela. Preencha com as suas
# (ex.: {"ong": "ONG", "tcc": "TCC"}); vazio, cada palavra só ganha inicial maiúscula.
_SIGLAS: dict = {}


@dataclass
class Objetivo:
    titulo: str
    slug: str
    texto: str
    projetos: list = field(default_factory=list)  # slugs de projetos/


def slug(texto: str) -> str:
    """`Viajar pro Canadá` -> `viajar-pro-canada`. Chave de casamento estável."""
    normal = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", normal.lower()).strip("-")


def nome_projeto(s: str) -> str:
    """`curso-de-violao` -> `Curso De Violao`, pra virar chip legível na tela."""
    palavras = s.split("-")
    saida = []
    for i, p in enumerate(palavras):
        if p in _SIGLAS:
            saida.append(_SIGLAS[p])
        elif p in _MINUSCULAS and i > 0:
            saida.append(p)
        else:
            saida.append(p.capitalize())
    return " ".join(saida)


def parse_objetivos(texto: str) -> list:
    """Cada `## Cabeçalho` (menos `## Nota`) vira um objetivo com seu texto e os
    projetos que ele linka."""
    objetivos: list = []
    titulo = None
    corpo: list = []

    def fechar():
        if titulo is None:
            return
        if slug(titulo) in _NAO_OBJETIVO:
            return
        texto_corpo = "\n".join(corpo).strip()
        projetos = []
        for p in _LINK_PROJETO.findall(texto_corpo):
            if p not in projetos:
                projetos.append(p)
        objetivos.append(Objetivo(titulo=titulo, slug=slug(titulo),
                                  texto=texto_corpo, projetos=projetos))

    for linha in texto.splitlines():
        m = _CABECALHO.match(linha)
        if m:
            fechar()
            titulo = m.group(1)
            corpo = []
        elif titulo is not None:
            corpo.append(linha)
    fechar()
    return objetivos


def indexar_tarefas(texto_tarefas: str):
    """Varre `tarefas.md` guardando a seção corrente. Devolve dois índices de
    tarefas **ativas** (não concluídas): por seção (slug do cabeçalho) e por
    objetivo marcado direto (`objetivo:<slug>`)."""
    por_secao: dict = {}
    por_objetivo: dict = {}
    atual = None
    for e in parse_tarefas(texto_tarefas):
        if isinstance(e, str):
            m = _CABECALHO.match(e)
            if m:
                atual = slug(m.group(1))
            continue
        if not isinstance(e, Tarefa) or e.concluida:
            continue
        if atual:
            por_secao[atual] = por_secao.get(atual, 0) + 1
        tag = (getattr(e, "objetivo", None) or "").strip()
        if tag:
            por_objetivo[tag] = por_objetivo.get(tag, 0) + 1
    return por_secao, por_objetivo


def _contar_projeto(por_secao: dict, projeto: str) -> int:
    """Casa o slug do projeto com o slug do cabeçalho da seção por subconjunto de
    palavras — `curso-violao` bate `## Curso de violão`, e `comprar-instrumento`
    bate `## Comprar instrumento` sem falso positivo."""
    alvo = set(projeto.split("-"))
    return sum(qtd for cab, qtd in por_secao.items()
               if alvo <= set(cab.split("-")))


def montar(texto_objetivos: str, texto_tarefas: str) -> list:
    """Junta os objetivos com o que está em andamento em cada um."""
    objetivos = parse_objetivos(texto_objetivos)
    por_secao, por_objetivo = indexar_tarefas(texto_tarefas)
    resultado = []
    for o in objetivos:
        via_projeto = sum(_contar_projeto(por_secao, p) for p in o.projetos)
        via_tag = por_objetivo.get(o.slug, 0)
        resultado.append({
            "titulo": o.titulo,
            "slug": o.slug,
            "texto": o.texto,
            "projetos": [{"slug": p, "nome": nome_projeto(p)} for p in o.projetos],
            "em_andamento": via_projeto + via_tag,
        })
    return resultado
