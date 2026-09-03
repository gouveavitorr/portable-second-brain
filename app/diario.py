"""Diário do que foi feito: parse e serialização de `second_brain/diario.md`.

Puro de propósito — nada aqui toca disco. O arquivo é do usuário e abre no Obsidian,
então o contrato é: só inserimos. Linha que este módulo não entende volta intacta na
serialização, igual `tasks.py` faz com `tarefas.md`.
"""

import re
from dataclasses import dataclass

CABECALHO = "# 📓 Diário"

_DIA = re.compile(r"^## (\d{4}-\d{2}-\d{2})\s*$")
_ANOTACAO = re.compile(r"^- (\d{2}:\d{2}) — (.*)$")
_ENERGIA_NO_FIM = re.compile(r"^(.*?)\s+\((leve|média|media|pesada)\)$")


@dataclass
class Anotacao:
    dia: str       # AAAA-MM-DD, vem do `## ` que abre a seção
    hora: str      # HH:MM de quando foi enviada
    texto: str
    energia: str | None = None


def limpar_texto(texto: str) -> str:
    """Uma anotação é uma linha. Quebra de linha viraria duas anotações no arquivo."""
    return " ".join(str(texto).split())


def parse_diario(texto: str) -> list:
    entradas: list = []
    dia_atual = None
    for linha in texto.splitlines():
        cabecalho = _DIA.match(linha)
        if cabecalho:
            dia_atual = cabecalho.group(1)
            entradas.append(linha)
            continue
        m = _ANOTACAO.match(linha)
        if not m or dia_atual is None:
            # sem dia aberto não dá pra datar a anotação: preserva como texto solto
            entradas.append(linha)
            continue
        corpo = m.group(2)
        energia = None
        com_energia = _ENERGIA_NO_FIM.match(corpo)
        if com_energia:
            corpo, energia = com_energia.group(1), com_energia.group(2)
        entradas.append(Anotacao(dia=dia_atual, hora=m.group(1),
                                 texto=corpo, energia=energia))
    return entradas


def serializar_linha(a: Anotacao) -> str:
    linha = f"- {a.hora} — {a.texto}"
    return f"{linha} ({a.energia})" if a.energia else linha


def serializar_diario(entradas: list) -> str:
    linhas = [serializar_linha(e) if isinstance(e, Anotacao) else e for e in entradas]
    if not linhas:
        return ""
    return "\n".join(linhas) + "\n"


def _indice_do_dia(entradas: list, dia: str) -> int | None:
    for i, e in enumerate(entradas):
        if isinstance(e, str):
            m = _DIA.match(e)
            if m and m.group(1) == dia:
                return i
    return None


def _indice_do_primeiro_dia(entradas: list) -> int | None:
    for i, e in enumerate(entradas):
        if isinstance(e, str) and _DIA.match(e):
            return i
    return None


def inserir(entradas: list, a: Anotacao) -> list:
    """Insere no topo do dia; dia novo entra no topo do arquivo (mais recente primeiro).

    Não reordena nada que já existe: só abre espaço.
    """
    novas = list(entradas)
    if not novas:
        novas = [CABECALHO, ""]

    i = _indice_do_dia(novas, a.dia)
    if i is not None:
        pos = i + 1
        while pos < len(novas) and novas[pos] == "":
            pos += 1
        novas.insert(pos, a)
        return novas

    bloco = [f"## {a.dia}", "", a, ""]
    destino = _indice_do_primeiro_dia(novas)
    if destino is None:
        # nenhum dia ainda: entra no fim, depois do cabeçalho
        while novas and novas[-1] == "":
            novas.pop()
        return novas + [""] + bloco[:-1]
    return novas[:destino] + bloco + novas[destino:]


def anotacoes_do_dia(entradas: list, dia: str) -> list:
    return [e for e in entradas if isinstance(e, Anotacao) and e.dia == dia]


def todas_anotacoes(entradas: list) -> list:
    return [e for e in entradas if isinstance(e, Anotacao)]
