"""Retrato do second brain: em que pé as coisas estão, agora.

Existe pra resolver um problema de sessão nova: o Claude (ou você, depois de uma
semana fora) abre o projeto sem saber o que está pendente, o que ficou pela metade
e o que já foi feito. Em vez de vasculhar arquivo por arquivo, roda isto:

    python -m scripts.estado              # imprime o retrato
    python -m scripts.estado --write      # também salva second_brain/estado.md

Só lê. Nunca escreve no vault fora do `estado.md`, e esse arquivo é gitignorado
justamente pra não sujar o working tree a cada sessão.

Sem dependência externa e sem rede de propósito: tem que rodar em 1 segundo, offline.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

# o console do Windows abre em cp1252 e mastiga os acentos do relatório
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
VAULT = RAIZ / "second_brain"

# quanto tempo cada cadência aguenta antes de virar "vencida"
JANELA = {"diario": 1, "semanal": 7, "mensal": 30}


def _ler(caminho: Path) -> str:
    try:
        return caminho.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _campos(linha: str) -> dict[str, str]:
    """`- [ ] Nome | prioridade:alta | feito:2026-07-23` -> dict + _nome."""
    partes = [p.strip() for p in linha.split("|")]
    nome = re.sub(r"^-\s*\[[ xX]\]\s*", "", partes[0]).strip()
    campos = {"_nome": nome}
    for p in partes[1:]:
        if ":" in p:
            k, _, v = p.partition(":")
            campos[k.strip()] = v.strip()
    return campos


def git() -> str:
    def run(*args: str) -> str:
        try:
            return subprocess.run(
                ["git", *args], cwd=RAIZ, capture_output=True, text=True, timeout=10
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""

    branch = run("rev-parse", "--abbrev-ref", "HEAD") or "?"
    sujo = run("status", "--porcelain")
    ultimo = run("log", "--oneline", "-1")
    estado = f"{len(sujo.splitlines())} arquivo(s) modificado(s)" if sujo else "limpo"
    return f"{branch} · {estado} · {ultimo}"


def tarefas() -> tuple[str, list[str]]:
    texto = _ler(VAULT / "tarefas.md")
    if not texto:
        return "tarefas.md não encontrado", []

    hoje = dt.date.today()
    total = 0
    vencidas: list[str] = []

    for linha in texto.splitlines():
        if not linha.strip().startswith("- ["):
            continue
        total += 1
        c = _campos(linha)
        repete = c.get("repete")
        if repete not in JANELA:
            continue
        feito = c.get("feito")
        if not feito:
            vencidas.append(f"{c['_nome']} ({repete}, nunca feita)")
            continue
        try:
            quando = dt.date.fromisoformat(feito)
        except ValueError:
            continue
        atraso = (hoje - quando).days
        if atraso >= JANELA[repete]:
            vencidas.append(f"{c['_nome']} ({repete}, há {atraso}d)")

    return f"{total} no total · {len(vencidas)} recorrente(s) vencida(s)", vencidas


def inbox() -> str:
    texto = _ler(VAULT / "inbox.md")
    if not texto:
        return "inbox.md não encontrado"
    # o conteúdo despejado fica depois do separador `---`
    _, sep, corpo = texto.partition("\n---")
    if not sep:
        return "sem separador `---` (formato inesperado)"
    itens = [
        l for l in corpo.splitlines()
        if l.strip()
        and not l.strip().startswith("#")
        and not l.strip().startswith("<!--")  # a dica "escreve abaixo desta linha" não é item
    ]
    return f"{len(itens)} item(ns) esperando /triagem" if itens else "vazio"


def diario() -> str:
    texto = _ler(VAULT / "diario.md")
    datas = re.findall(r"^##\s*(\d{4}-\d{2}-\d{2})", texto, re.MULTILINE)
    if not datas:
        return "sem entradas"
    ultima = datas[0]
    dias = (dt.date.today() - dt.date.fromisoformat(ultima)).days
    quando = "hoje" if dias == 0 else "ontem" if dias == 1 else f"há {dias} dias"
    # registros sob a data mais recente
    bloco = texto.split(f"## {ultima}", 1)[-1].split("\n## ", 1)[0]
    n = len([l for l in bloco.splitlines() if l.strip().startswith("-")])
    return f"última entrada {quando} ({ultima}) · {n} registro(s)"


def contar(pasta: str, padrao: str = "*.md") -> int:
    p = VAULT / pasta
    return len([f for f in p.rglob(padrao) if not f.name.startswith("_")]) if p.is_dir() else 0


def montar() -> str:
    agora = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    t_resumo, t_vencidas = tarefas()

    L = [f"ESTADO DO SECOND BRAIN — {agora}", ""]
    L.append(f"  git        {git()}")
    L.append(f"  inbox      {inbox()}")
    L.append(f"  diário     {diario()}")
    L.append(f"  tarefas    {t_resumo}")
    for v in t_vencidas:
        L.append(f"               · {v}")
    L.append(f"  áreas      {contar('areas')} arquivo(s)")
    L.append("")
    L.append("  Fluxo e filosofia: second_brain/index.md · Convenções: CLAUDE.md")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="Retrato do estado do second brain.")
    ap.add_argument(
        "--write", action="store_true",
        help="também salva em second_brain/estado.md (gitignorado)",
    )
    args = ap.parse_args()

    retrato = montar()
    print(retrato)

    if args.write:
        destino = VAULT / "estado.md"
        destino.write_text(
            "# Estado\n\nGerado por `python -m scripts.estado --write`. "
            "Não edite à mão: é sobrescrito.\n\n```\n" + retrato + "\n```\n",
            encoding="utf-8",
        )
        print(f"\n-> {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
