from datetime import date
from app.tasks import Tarefa

_PRIORIDADE_RANK = {"alta": 0, "media": 1, "baixa": 2}

# Quanto tempo uma tarefa provavelmente pede, quando ela não traz `min`.
MIN_ESTIMADO = {"leve": 10, "media": 20, "pesada": 45}

# De quantos em quantos dias uma tarefa recorrente volta a aparecer.
PERIODO_DIAS = {"diario": 1, "semanal": 7, "mensal": 30}


def disponivel(t: Tarefa, hoje: date) -> bool:
    """A tarefa pode aparecer hoje?

    Só diz respeito a recorrentes: uma diária feita hoje some até amanhã.
    Pular dias não gera penalidade nenhuma — a tarefa só volta a ficar disponível.
    """
    if not t.repete or not t.feito:
        return True
    try:
        feito = date.fromisoformat(t.feito)
    except ValueError:
        return True  # data escrita à mão e torta: melhor mostrar que sumir
    dias = PERIODO_DIAS.get(t.repete, 1)
    return (hoje - feito).days >= dias


def dias_para_voltar(t: Tarefa, hoje: date) -> int:
    """Quantos dias faltam pra recorrente reativar. 0 = já disponível.

    Alimenta o "volta em Xd" da coluna de recorrentes.
    """
    if not t.repete or not t.feito:
        return 0
    try:
        feito = date.fromisoformat(t.feito)
    except ValueError:
        return 0
    dias = PERIODO_DIAS.get(t.repete, 1)
    return max(0, dias - (hoje - feito).days)


def minutos_de(t: Tarefa) -> int:
    """Quanto a tarefa pede: o `min` dela, ou a estimativa pela energia."""
    if t.min is not None:
        return t.min
    # o .md é editado à mão: energia desconhecida cai na estimativa média
    return MIN_ESTIMADO.get(t.energia or "media", MIN_ESTIMADO["media"])


def cabe_na_janela(t: Tarefa, janela) -> bool:
    """A tarefa cabe no tempo livre até o próximo compromisso?

    `janela=None` significa sem compromissos: tudo cabe.
    """
    if janela is None:
        return True
    return minutos_de(t) <= janela


def _rank_prazo(t: Tarefa, hoje: date) -> int:
    if not t.prazo:
        return 2  # sem prazo por último
    try:
        d = date.fromisoformat(t.prazo)
    except ValueError:
        return 2
    if d <= hoje:
        return 0  # vencida ou hoje
    return 1  # futura


def _rank_prioridade(t: Tarefa) -> int:
    return _PRIORIDADE_RANK.get(t.prioridade or "media", 1)


def _chave_normal(item, hoje: date):
    idx, t = item
    return (_rank_prazo(t, hoje), _rank_prioridade(t), idx)


def _chave_facil(item, hoje: date):
    idx, t = item
    leve = 0 if t.energia == "leve" else 1
    minutos = t.min if t.min is not None else float("inf")
    urgente = 0 if _rank_prazo(t, hoje) == 0 else 1
    return (urgente, leve, minutos, idx)


def escolher_agora(tarefas, hoje: date, modo_facil: bool = False,
                   offset: int = 0, n: int = 3, janela=None):
    # recorrentes têm coluna própria: nunca entram no "Escolha uma pra começar".
    abertas = [(i, t) for i, t in enumerate(tarefas)
               if not t.concluida and not t.repete and disponivel(t, hoje)]
    chave = _chave_facil if modo_facil else _chave_normal
    ordenadas = [t for _, t in sorted(abertas, key=lambda it: chave(it, hoje))]
    if janela is not None:
        cabem = [t for t in ordenadas if cabe_na_janela(t, janela)]
        # se nada cabe, volta à ordem normal: tela vazia prenderia o usuário
        ordenadas = cabem or ordenadas
    L = len(ordenadas)
    if L == 0:
        return []
    if L <= n:
        return ordenadas
    inicio = offset % L
    return [ordenadas[(inicio + k) % L] for k in range(n)]
