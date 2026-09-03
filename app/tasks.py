import re
import secrets
from dataclasses import dataclass

_LINHA_TAREFA = re.compile(r"^- \[( |x)\] (.*)$")
_CAMPOS_CONHECIDOS = {"prioridade", "energia", "passo", "prazo", "min",
                      "repete", "feito", "id", "objetivo"}


@dataclass
class Tarefa:
    titulo: str
    concluida: bool = False
    prioridade: str | None = None
    energia: str | None = None
    passo: str | None = None
    prazo: str | None = None
    min: int | None = None
    repete: str | None = None   # diario | semanal | mensal
    feito: str | None = None    # AAAA-MM-DD da última vez que a recorrente saiu
    objetivo: str | None = None  # slug de um objetivo que esta task empurra direto
    id: str | None = None


def gerar_id() -> str:
    return secrets.token_hex(2)  # 4 chars hex


def parse_tarefas(texto: str) -> list:
    entradas: list = []
    for linha in texto.splitlines():
        m = _LINHA_TAREFA.match(linha)
        if not m:
            entradas.append(linha)
            continue
        concluida = m.group(1) == "x"
        resto = m.group(2)
        partes = [p.strip() for p in resto.split("|")]
        titulo = partes[0]
        t = Tarefa(titulo=titulo, concluida=concluida)
        for seg in partes[1:]:
            if ":" not in seg:
                continue
            chave, _, valor = seg.partition(":")
            chave = chave.strip()
            valor = valor.strip()
            if chave not in _CAMPOS_CONHECIDOS:
                continue
            if chave == "min":
                try:
                    t.min = int(valor)
                except ValueError:
                    pass
            else:
                setattr(t, chave, valor)
        entradas.append(t)
    return entradas


def serializar_linha(t: Tarefa) -> str:
    marca = "x" if t.concluida else " "
    partes = [f"- [{marca}] {t.titulo}"]
    if t.prioridade:
        partes.append(f"prioridade:{t.prioridade}")
    if t.energia:
        partes.append(f"energia:{t.energia}")
    if t.passo:
        partes.append(f"passo: {t.passo}")
    if t.prazo:
        partes.append(f"prazo:{t.prazo}")
    if t.min is not None:
        partes.append(f"min:{t.min}")
    if t.repete:
        partes.append(f"repete:{t.repete}")
    if t.feito:
        partes.append(f"feito:{t.feito}")
    if t.objetivo:
        partes.append(f"objetivo:{t.objetivo}")
    if t.id:
        partes.append(f"id:{t.id}")
    return " | ".join(partes)


def serializar_tarefas(entradas: list) -> str:
    linhas = [serializar_linha(e) if isinstance(e, Tarefa) else e for e in entradas]
    if not linhas:
        return ""
    return "\n".join(linhas) + "\n"


def garantir_ids(entradas: list) -> bool:
    mudou = False
    existentes = {e.id for e in entradas if isinstance(e, Tarefa) and e.id}
    for e in entradas:
        if isinstance(e, Tarefa) and not e.id:
            novo = gerar_id()
            while novo in existentes:
                novo = gerar_id()
            e.id = novo
            existentes.add(novo)
            mudou = True
    return mudou
