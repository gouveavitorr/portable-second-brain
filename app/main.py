import os
import subprocess
import sys
import threading
import time
from datetime import date, datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.storage import Vault
from app.pokemon import ClientePokeAPI
from app.servico import Servico
from app.tasks import Tarefa
from app.financeiro import num
from app.dieta import so_massa
from app.calendario import ja_passou
from app.engine import escolher_agora, minutos_de, disponivel, dias_para_voltar

_STATIC = Path(__file__).resolve().parent.parent / "static"
_RAIZ = Path(__file__).resolve().parent.parent


def _encerrar_em_breve(delay: float = 0.3) -> None:
    """Cai depois de responder. O endpoint devolve a resposta, e um instante depois
    o processo encerra — assim a tela consegue reagir antes de o servidor sumir.
    Local e mono-usuário: derrubar o processo assim é seguro (o vault grava atômico).
    """
    def alvo() -> None:
        time.sleep(delay)
        os._exit(0)
    threading.Thread(target=alvo, daemon=True).start()


def _disparar_reiniciar() -> None:
    """Sobe um ajudante solto que espera este servidor cair e sobe outro no lugar.

    Sem janela (CREATE_NO_WINDOW). O handoff da porta mora no `abrir.py --reiniciar`.
    """
    sem_janela = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen(
        [sys.executable, str(_RAIZ / "abrir.py"), "--reiniciar"],
        cwd=str(_RAIZ),
        creationflags=sem_janela,
    )


def _tarefa_dict(t: Tarefa, hoje: date) -> dict:
    return {
        "id": t.id,
        "titulo": t.titulo,
        "concluida": t.concluida,
        "prioridade": t.prioridade,
        "energia": t.energia,
        "passo": t.passo,
        "prazo": t.prazo,
        "min": t.min,
        "repete": t.repete,
        "feito": t.feito,
        # estado da recorrente pra coluna: se cabe hoje e, se não, quantos dias faltam
        "disponivel": disponivel(t, hoje),
        "volta_em": dias_para_voltar(t, hoje),
        # o que a tela mostra como custo: `min` quando existe, senão a estimativa
        # do motor. `estimado` evita a tela vender chute como fato.
        "min_efetivo": minutos_de(t),
        "estimado": t.min is None,
    }


def _anotacao_dict(a) -> dict:
    return {"dia": a.dia, "hora": a.hora, "texto": a.texto, "energia": a.energia}


def _evento_dict(e, agora=None) -> dict:
    return {
        "titulo": e.titulo,
        "inicio": e.inicio.strftime("%H:%M"),
        "fim": e.fim.strftime("%H:%M"),
        "dia_inteiro": e.dia_inteiro,
        "passado": ja_passou(e, agora) if agora else False,
    }


_num = num


def _entrada_dict(e) -> dict:
    return {
        "id": e.id, "nome": e.nome, "valor": _num(e.valor),
        "pago": e.pago, "pausado": e.pausado, "obs": e.obs,
    }


def _conta_dict(c) -> dict:
    return {
        "id": c.id, "nome": c.nome, "parcela": c.parcela,
        "valor": _num(c.valor), "faltante": _num(c.faltante), "pago": c.pago,
    }


def _fixo_dict(f) -> dict:
    return {"id": f.id, "nome": f.nome, "valor": _num(f.valor), "pago": f.pago}


def _gasto_dict(g) -> dict:
    return {"id": g.id, "local": g.local, "data": g.data, "valor": _num(g.valor)}


def _item_dict(i) -> dict:
    # `qtd_massa` é o que a tela mostra: só grama/ml, sem colher nem concha.
    # `qtd` continua cru porque é o que está escrito no .md.
    return {"nome": i.nome, "qtd": i.qtd, "qtd_massa": so_massa(i.qtd),
            "kcal": i.kcal, "cat": i.cat}


def _sub_dict(s) -> dict:
    return {
        "titulo": s.titulo, "itens": [_item_dict(i) for i in s.itens], "obs": s.obs,
        "kcal": round(sum(_num(i.kcal) for i in s.itens), 1),
    }


def _refeicao_dict(r) -> dict:
    return {
        "hora": r.hora, "nome": r.nome,
        "itens": [_item_dict(i) for i in r.itens], "obs": r.obs,
        "subs": [_sub_dict(s) for s in r.subs],
        "kcal": round(sum(_num(i.kcal) for i in r.itens), 1),
    }


def _corpo_dict(c) -> dict:
    return {
        "antes": c.antes, "agora": c.agora, "nota": c.nota,
        "grupos": [
            {"titulo": g.titulo, "legenda": g.legenda,
             "medidas": [{"nome": m.nome, "antes": m.antes,
                          "agora": m.agora, "delta": m.delta} for m in g.medidas]}
            for g in c.grupos
        ],
    }


def _compra_dict(c) -> dict:
    return {"id": c.id, "nome": c.nome, "qtd": c.qtd, "qtd_massa": so_massa(c.qtd),
            "nota": c.nota, "freq": c.freq, "comprado": c.comprado, "grupo": c.grupo}


def criar_app(servico: Servico) -> FastAPI:
    app = FastAPI(title="Second Brain")

    if _STATIC.is_dir():
        app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")

    @app.middleware("http")
    async def sem_cache_na_tela(request, call_next):
        # a tela é servida do disco e editada à mão: o navegador precisa revalidar
        # sempre, senão fica preso num app.js/style.css antigo depois de um deploy.
        resposta = await call_next(request)
        caminho = request.url.path
        if caminho == "/" or caminho.startswith("/static"):
            resposta.headers["Cache-Control"] = "no-cache"
        return resposta

    @app.get("/")
    def index():
        return FileResponse(str(_STATIC / "index.html"))

    @app.get("/api/tarefas")
    def listar():
        hoje = servico.hoje()
        return {"tarefas": [_tarefa_dict(t, hoje) for t in servico.listar_tarefas()]}

    @app.post("/api/tarefas", status_code=201)
    def adicionar(dados: dict):
        if not dados.get("titulo"):
            raise HTTPException(400, "titulo é obrigatório")
        return _tarefa_dict(servico.adicionar_tarefa(dados), servico.hoje())

    @app.patch("/api/tarefas/{id}")
    def editar(id: str, mudancas: dict):
        t = servico.editar_tarefa(id, mudancas)
        if t is None:
            raise HTTPException(404, "tarefa não encontrada")
        return _tarefa_dict(t, servico.hoje())

    @app.get("/api/agora")
    def agora(modo_facil: bool = False, offset: int = 0):
        tarefas = servico.listar_tarefas()
        cal = servico.estado_calendario()
        hoje = servico.hoje()
        escolhidas = escolher_agora(tarefas, hoje=hoje,
                                    modo_facil=modo_facil, offset=offset,
                                    janela=cal["janela_livre"])
        return {"tarefas": [_tarefa_dict(t, hoje) for t in escolhidas],
                "janela_livre": cal["janela_livre"]}

    @app.get("/api/eventos")
    def eventos():
        cal = servico.estado_calendario()
        agora = servico.agora()
        return {
            "eventos": [_evento_dict(e, agora) for e in cal["eventos"]],
            "janela_livre": cal["janela_livre"],
            "evento_atual": _evento_dict(cal["evento_atual"]) if cal["evento_atual"] else None,
            "configurado": cal["configurado"],
        }

    @app.post("/api/diario", status_code=201)
    def anotar(dados: dict):
        try:
            a = servico.anotar(dados.get("texto", ""), dados.get("energia"))
        except ValueError:
            raise HTTPException(400, "texto é obrigatório")
        return _anotacao_dict(a)

    @app.get("/api/diario")
    def diario(dia: str | None = None):
        return {"anotacoes": [_anotacao_dict(a) for a in servico.listar_anotacoes(dia)]}

    @app.get("/api/pokemon")
    def pokemon():
        return servico.estado_pokemon()

    # ---- financeiro ----
    @app.get("/financeiro")
    def financeiro_page():
        return FileResponse(str(_STATIC / "financeiro.html"))

    @app.get("/api/financeiro")
    def api_financeiro():
        d = servico.listar_financeiro()
        recebimentos, contas = d["recebimentos"], d["contas"]
        ativos = [e for e in recebimentos if not e.pausado]
        return {
            "recebimentos": [_entrada_dict(e) for e in recebimentos],
            "fixos": [_fixo_dict(f) for f in d["fixos"]],
            "contas": [_conta_dict(c) for c in contas],
            "gastos": [_gasto_dict(g) for g in d["gastos"]],
            "totais": {
                **d["resumo"],
                "ativos": len(ativos),
                "esperado": sum(_num(e.valor) for e in ativos),
                "recebido": sum(_num(e.valor) for e in ativos if e.pago),
                "pagos": sum(1 for e in ativos if e.pago),
                "contas_total": sum(_num(c.valor) for c in contas),
                # o acionável do mês: parcelas deste mês ainda não marcadas como pagas
                "contas_a_pagar": sum(_num(c.valor) for c in contas if not c.pago),
                # saldo das parcelas futuras (não é deste mês)
                "contas_faltante": sum(_num(c.faltante) for c in contas),
            },
        }

    @app.patch("/api/financeiro/entrada/{id}")
    def patch_entrada(id: str, mudancas: dict):
        e = servico.editar_entrada(id, mudancas)
        if e is None:
            raise HTTPException(404, "entrada não encontrada")
        return _entrada_dict(e)

    @app.patch("/api/financeiro/conta/{id}")
    def patch_conta(id: str, mudancas: dict):
        c = servico.editar_conta(id, mudancas)
        if c is None:
            raise HTTPException(404, "conta não encontrada")
        return _conta_dict(c)

    @app.patch("/api/financeiro/fixo/{id}")
    def patch_fixo(id: str, mudancas: dict):
        f = servico.editar_fixo(id, mudancas)
        if f is None:
            raise HTTPException(404, "fixo não encontrado")
        return _fixo_dict(f)

    @app.patch("/api/financeiro/mes")
    def patch_mes(mudancas: dict):
        try:
            valor = float(str(mudancas["guardado"]).replace(",", "."))
        except (KeyError, TypeError, ValueError):
            raise HTTPException(400, "guardado precisa ser um número")
        return servico.definir_guardado(round(valor, 2))

    @app.get("/api/metas")
    def api_metas():
        return {"metas": servico.estado_metas()}

    @app.patch("/api/metas/{chave}")
    def patch_meta(chave: str, mudancas: dict):
        try:
            valor = float(str(mudancas["valor"]).replace(",", "."))
        except (KeyError, TypeError, ValueError):
            raise HTTPException(400, "valor precisa ser um número")
        try:
            return {"metas": servico.definir_guardado_meta(chave, round(valor, 2))}
        except ValueError:
            raise HTTPException(404, "meta não encontrada")

    @app.post("/api/metas/{chave}/deposito")
    def post_deposito(chave: str, dados: dict):
        try:
            valor = float(str(dados["valor"]).replace(",", "."))
        except (KeyError, TypeError, ValueError):
            raise HTTPException(400, "valor precisa ser um número")
        if valor <= 0:
            raise HTTPException(400, "o depósito precisa ser positivo")
        try:
            return {"metas": servico.depositar_meta(chave, round(valor, 2))}
        except ValueError:
            raise HTTPException(404, "meta não encontrada")

    @app.post("/api/financeiro/gasto", status_code=201)
    def post_gasto(dados: dict):
        try:
            g = servico.adicionar_gasto(dados)
        except ValueError:
            raise HTTPException(400, "local é obrigatório")
        return _gasto_dict(g)

    # ---- dieta ----
    @app.get("/dieta")
    def dieta_page():
        return FileResponse(str(_STATIC / "dieta.html"))

    @app.get("/api/dieta")
    def api_dieta():
        d = servico.listar_dieta()
        compras = d["compras"]
        return {
            "refeicoes": [_refeicao_dict(r) for r in d["refeicoes"]],
            "compras": [_compra_dict(c) for c in compras],
            "corpo": _corpo_dict(d["corpo"]),
            "notas": d["notas"],
            "totais": {
                "kcal_dia": round(sum(_num(i.kcal)
                                      for r in d["refeicoes"] for i in r.itens), 1),
                "itens": len(compras),
                "comprados": sum(1 for c in compras if c.comprado),
            },
        }

    @app.patch("/api/dieta/compra/{id}")
    def patch_compra(id: str, mudancas: dict):
        c = servico.marcar_compra(id, bool(mudancas.get("comprado")))
        if c is None:
            raise HTTPException(404, "item não encontrado")
        return _compra_dict(c)

    @app.post("/api/dieta/inbox", status_code=201)
    def post_inbox_dieta(dados: dict):
        try:
            return servico.despejar_dieta(dados.get("texto"))
        except ValueError:
            raise HTTPException(400, "texto é obrigatório")

    # ---- objetivos ----
    @app.get("/objetivos")
    def objetivos_page():
        return FileResponse(str(_STATIC / "objetivos.html"))

    @app.get("/api/objetivos")
    def api_objetivos():
        return {"objetivos": servico.listar_objetivos()}

    # ---- inbox ----
    @app.get("/api/inbox")
    def api_inbox():
        return {"pendentes": servico.contar_inbox()}

    @app.post("/api/inbox", status_code=201)
    def post_inbox(dados: dict):
        """Captura rápida da tela Agora: uma linha, sem confirmação, sem sair."""
        try:
            return servico.despejar_inbox(dados.get("texto"))
        except ValueError:
            raise HTTPException(400, "texto é obrigatório")

    @app.post("/api/desligar")
    def desligar():
        """Encerra o app. Substitui o "fechar a janela do console" que sumiu."""
        _encerrar_em_breve()
        return {"desligando": True}

    @app.post("/api/reiniciar")
    def reiniciar():
        """Sobe um servidor novo e encerra este. Ordem importa: dispara o ajudante
        antes de agendar a própria saída, senão ninguém sobe o substituto."""
        _disparar_reiniciar()
        _encerrar_em_breve()
        return {"reiniciando": True}

    return app


def _app_default() -> FastAPI:
    vault = Vault(Path("second_brain"))
    vault.garantir()
    cliente = ClientePokeAPI(vault.cache_dir)
    # Portátil: sem calendário externo. O app roda sem consciência de tempo
    # (Servico com calendario=None); a tela "Agora" só perde a janela livre.
    return criar_app(Servico(vault, cliente))


app = _app_default()
