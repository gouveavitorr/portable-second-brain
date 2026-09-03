"""Parser e serialização de `second_brain/financeiro.md`.

Puro: nada aqui toca disco. Mesmo contrato de `tasks.py`/`diario.py` — linha que o
módulo não entende volta intacta na serialização, então o arquivo abre no Obsidian sem
susto. As seções `## Recebimentos`, `## Fixos`, `## Contas` e `## Gastos` decidem o
tipo de cada linha `- `.
"""

import re
import secrets
from dataclasses import dataclass

_LINHA = re.compile(r"^- (.*)$")
_SECAO = re.compile(r"^##\s+(.*?)\s*$")


@dataclass
class Entrada:
    """O que entra no mês: salário, contrato, um cliente, uma mesada. Genérico de
    propósito — cada pessoa preenche do jeito dela. `valor` é o esperado no mês."""
    nome: str
    valor: str | None = None     # R$ no mês
    pago: str | None = None      # AAAA-MM-DDTHH:MM de quando entrou/foi recebido
    pausado: bool = False        # entrada que não vale este mês
    obs: str | None = None
    id: str | None = None


@dataclass
class Conta:
    nome: str
    parcela: str | None = None   # ex "1/2"
    valor: str | None = None     # R$ deste mês
    faltante: str | None = None  # R$ que ainda falta
    pago: str | None = None
    id: str | None = None


@dataclass
class Fixo:
    """Gasto que se repete todo mês e nunca acaba — é ele que forma o custo fixo.

    Diferente de `Conta`, que é parcelamento com fim marcado.
    """
    nome: str
    valor: str | None = None     # R$ por mês
    pago: str | None = None
    id: str | None = None


@dataclass
class Gasto:
    local: str
    data: str | None = None      # AAAA-MM-DD
    valor: str | None = None
    id: str | None = None


@dataclass
class Mes:
    """Números do mês que não saem de nenhuma outra linha. Hoje só `guardado`."""
    nome: str
    valor: str | None = None
    id: str | None = None


# qual seção vira qual tipo, e qual é o primeiro campo (o "título" da linha)
_TIPOS = {
    "recebimentos": (Entrada, "nome"),
    "fixos": (Fixo, "nome"),
    "contas": (Conta, "nome"),
    "gastos": (Gasto, "local"),
    "mês": (Mes, "nome"),
    "mes": (Mes, "nome"),        # o .md é escrito à mão; aceita sem acento
}
_CAMPOS = {
    Entrada: {"valor", "pago", "pausado", "obs", "id"},
    Fixo: {"valor", "pago", "id"},
    Conta: {"parcela", "valor", "faltante", "pago", "id"},
    Gasto: {"data", "valor", "id"},
    Mes: {"valor", "id"},
}


def gerar_id() -> str:
    return secrets.token_hex(2)


def num(s) -> float:
    # o .md é editado à mão e usa vírgula decimal (ex "1,5"); sem separador de milhar.
    try:
        return float(str(s).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0


def _secao_de(titulo: str) -> str | None:
    t = titulo.strip().lower()
    return t if t in _TIPOS else None


def parse_financeiro(texto: str) -> list:
    entradas: list = []
    tipo = None
    for linha in texto.splitlines():
        cab = _SECAO.match(linha)
        if cab:
            tipo = _secao_de(cab.group(1))
            entradas.append(linha)
            continue
        m = _LINHA.match(linha)
        if not m or tipo is None:
            entradas.append(linha)
            continue
        cls, campo_nome = _TIPOS[tipo]
        partes = [p.strip() for p in m.group(1).split("|")]
        obj = cls(**{campo_nome: partes[0]})
        for seg in partes[1:]:
            chave, sep, valor = seg.partition(":")
            chave = chave.strip()
            valor = valor.strip()
            if chave not in _CAMPOS[cls]:
                continue
            if chave == "pausado":
                obj.pausado = valor.lower() in ("sim", "true", "1", "")
            else:
                setattr(obj, chave, valor or None)
        entradas.append(obj)
    return entradas


def _campos_ordem(obj) -> list[tuple[str, str]]:
    if isinstance(obj, Entrada):
        pares = [("valor", obj.valor), ("pago", obj.pago)]
        if obj.pausado:
            pares.append(("pausado", "sim"))
        pares += [("obs", obj.obs), ("id", obj.id)]
        return [(k, v) for k, v in pares if v]
    if isinstance(obj, Conta):
        pares = [("parcela", obj.parcela), ("valor", obj.valor),
                 ("faltante", obj.faltante), ("pago", obj.pago), ("id", obj.id)]
        return [(k, v) for k, v in pares if v]
    if isinstance(obj, Fixo):
        pares = [("valor", obj.valor), ("pago", obj.pago), ("id", obj.id)]
        return [(k, v) for k, v in pares if v]
    if isinstance(obj, Mes):
        pares = [("valor", obj.valor), ("id", obj.id)]
        return [(k, v) for k, v in pares if v]
    pares = [("data", obj.data), ("valor", obj.valor), ("id", obj.id)]
    return [(k, v) for k, v in pares if v]


def _nome_de(obj) -> str:
    return obj.local if isinstance(obj, Gasto) else obj.nome


def serializar_linha(obj) -> str:
    partes = [f"- {_nome_de(obj)}"]
    for chave, valor in _campos_ordem(obj):
        partes.append(f"{chave}:{valor}")
    return " | ".join(partes)


def serializar_financeiro(entradas: list) -> str:
    linhas = [serializar_linha(e) if not isinstance(e, str) else e for e in entradas]
    if not linhas:
        return ""
    return "\n".join(linhas) + "\n"


def garantir_ids(entradas: list) -> bool:
    mudou = False
    existentes = {e.id for e in entradas if not isinstance(e, str) and e.id}
    for e in entradas:
        # `Mes` é endereçada pelo nome, não por id — não suja a linha com um
        if isinstance(e, (str, Mes)) or e.id:
            continue
        novo = gerar_id()
        while novo in existentes:
            novo = gerar_id()
        e.id = novo
        existentes.add(novo)
        mudou = True
    return mudou


def linha_mes(entradas: list, nome: str) -> Mes | None:
    """Uma linha da seção `## Mês` achada pelo nome (case-insensitive)."""
    alvo = nome.strip().lower()
    return next((e for e in entradas
                 if isinstance(e, Mes) and e.nome.strip().lower() == alvo), None)


def guardado_de(entradas: list) -> Mes | None:
    """A linha `- guardado` da seção `## Mês`, se existir."""
    return linha_mes(entradas, "guardado")


MESES_RESERVA = 7   # quantos meses de custo fixo a reserva precisa cobrir


def resumo(entradas: list) -> dict:
    """Os números que o mês inteiro responde: quanto custa viver e quanto já tem guardado.

    `custo_fixo` sai só de `## Fixos` — parcelamento acaba, então não conta. `renda`
    ignora entrada pausada, que por definição não vale este mês. `guardado` é o total
    acumulado, não o do mês: a meta (`custo_fixo × 7`) também é um total.
    """
    custo_fixo = sum(num(e.valor) for e in entradas if isinstance(e, Fixo))
    renda = sum(num(e.valor) for e in entradas
                if isinstance(e, Entrada) and not e.pausado)
    linha = guardado_de(entradas)
    guardado = num(linha.valor) if linha else 0.0
    meta = custo_fixo * MESES_RESERVA
    return {
        "custo_fixo": custo_fixo,
        "renda": renda,
        "guardado": guardado,
        "meta_guardado": meta,
        "falta_guardar": max(meta - guardado, 0.0),
        # a barra não passa de 100: guardar além da meta não é "mais que cheio"
        "pct_guardado": min(round(guardado / meta * 100), 100) if meta else 0,
    }


# --- Metas que viram companheiro na tela Agora ---
# A reserva tem meta dinâmica (custo fixo × 7) e vem de fábrica, porque todo mundo
# se beneficia de um fundo de emergência. Metas fixas (uma viagem, um objeto caro)
# são pessoais: cada um adiciona a sua aqui, com o alvo em R$ e o slug do Pokémon
# da PokeAPI. Exemplo comentado abaixo.
META_RESERVA = {"chave": "reserva", "rotulo": "reserva",
                "linha": "guardado", "pokemon": "togepi"}
METAS_FIXAS: list = [
    # {"chave": "viagem", "rotulo": "Viagem", "linha": "viagem",
    #  "meta": 7000.0, "pokemon": "vulpix-alola"},
]
# chave da meta -> nome da linha no `## Mês` onde o valor guardado é gravado
LINHA_META = {m["chave"]: m["linha"] for m in [META_RESERVA, *METAS_FIXAS]}


def _meta_dict(chave, rotulo, guardado, meta, pokemon) -> dict:
    guardado = max(num(guardado), 0.0)
    meta = num(meta)
    return {
        "chave": chave, "rotulo": rotulo, "pokemon": pokemon,
        "guardado": guardado, "meta": meta,
        "falta": max(meta - guardado, 0.0),
        # a barra não passa de 100: guardar além da meta não é "mais que cheio"
        "pct": min(round(guardado / meta * 100), 100) if meta else 0,
    }


def metas(entradas: list) -> list:
    """As metas na ordem da tela: reserva (esquerda) e as fixas depois. Cada uma traz
    quanto tem, quanto é a meta e o Pokémon — o sprite é colado na camada de serviço."""
    r = resumo(entradas)
    saida = [_meta_dict(META_RESERVA["chave"], META_RESERVA["rotulo"],
                        r["guardado"], r["meta_guardado"], META_RESERVA["pokemon"])]
    for m in METAS_FIXAS:
        linha = linha_mes(entradas, m["linha"])
        guardado = num(linha.valor) if linha else 0.0
        saida.append(_meta_dict(m["chave"], m["rotulo"], guardado,
                                m["meta"], m["pokemon"]))
    return saida


def indice_secao(entradas: list, nome: str) -> int | None:
    """Índice da linha `## <nome>` (case-insensitive), pra inserir dentro da seção."""
    alvo = nome.strip().lower()
    for i, e in enumerate(entradas):
        if isinstance(e, str):
            m = _SECAO.match(e)
            if m and m.group(1).strip().lower() == alvo:
                return i
    return None
