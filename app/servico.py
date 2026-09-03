import json
import random
from datetime import datetime
from app.storage import ler_texto, escrever_texto_atomico
from app.tasks import (
    Tarefa, parse_tarefas, serializar_tarefas, garantir_ids,
)
from app.pokemon import (
    Progresso, xp_por_energia, aplicar_xp, limiar_do_estagio, nome_bonito,
)
from app.calendario import janela_livre, evento_atual
from app.diario import (
    Anotacao, parse_diario, serializar_diario, inserir, limpar_texto,
    anotacoes_do_dia, todas_anotacoes,
)
from app.financeiro import (
    Entrada, Conta, Fixo, Gasto, Mes, parse_financeiro, serializar_financeiro,
    garantir_ids as garantir_ids_fin, guardado_de, linha_mes, indice_secao,
    num, resumo, metas, LINHA_META,
)
from app.dieta import (
    Compra, parse_dieta, serializar_dieta, refeicoes_de, corpo_de,
    garantir_ids as garantir_ids_dieta,
)
from app.objetivos import montar as montar_objetivos

_CAMPOS_TAREFA = {"titulo", "prioridade", "energia", "passo", "prazo", "min",
                  "repete", "feito", "concluida"}

_ENERGIAS = {"leve": "leve", "media": "média", "média": "média", "pesada": "pesada"}


_MARCADOR_INBOX = "<!-- escreve abaixo desta linha -->"

_SECAO_INBOX_DIETA = "## Inbox da dieta"


class Servico:
    def __init__(self, vault, cliente, rng=None, calendario=None, agora=None):
        self.vault = vault
        self.cliente = cliente
        self.rng = rng or random.Random()
        self.calendario = calendario
        self._agora = agora or datetime.now

    def agora(self):
        return self._agora()

    def hoje(self):
        return self._agora().date()

    # ---- calendário (opcional: None = sem consciência de tempo, o padrão portátil) ----
    def estado_calendario(self):
        if self.calendario is None:
            return {"eventos": [], "janela_livre": None,
                    "evento_atual": None, "configurado": False}
        agora = self.agora()
        eventos = self.calendario.eventos_de_hoje(agora.date())
        return {
            "eventos": eventos,
            "janela_livre": janela_livre(eventos, agora),
            "evento_atual": evento_atual(eventos, agora),
            "configurado": self.calendario.configurado,
        }

    # ---- tarefas ----
    def _ler_entradas(self):
        entradas = parse_tarefas(ler_texto(self.vault.tarefas_md))
        if garantir_ids(entradas):
            escrever_texto_atomico(self.vault.tarefas_md, serializar_tarefas(entradas))
        return entradas

    def _salvar_entradas(self, entradas):
        escrever_texto_atomico(self.vault.tarefas_md, serializar_tarefas(entradas))

    def listar_tarefas(self):
        return [e for e in self._ler_entradas() if isinstance(e, Tarefa)]

    def adicionar_tarefa(self, dados):
        entradas = self._ler_entradas()
        t = Tarefa(titulo=dados["titulo"])
        for k in ("prioridade", "energia", "passo", "prazo", "repete"):
            if dados.get(k):
                setattr(t, k, dados[k])
        if dados.get("min") is not None:
            t.min = int(dados["min"])
        entradas.append(t)
        garantir_ids(entradas)
        self._salvar_entradas(entradas)
        return t

    def editar_tarefa(self, id, mudancas):
        entradas = self._ler_entradas()
        alvo = next((e for e in entradas
                     if isinstance(e, Tarefa) and e.id == id), None)
        if alvo is None:
            return None
        hoje = self.hoje().isoformat()
        if alvo.repete:
            # recorrente: nunca vira [x] pra sempre. só registra que saiu hoje
            # e some do "Agora" até o período virar.
            concluir = (mudancas.get("concluida") is True and alvo.feito != hoje)
            mudancas = {k: v for k, v in mudancas.items() if k != "concluida"}
            if concluir:
                alvo.feito = hoje
        else:
            concluir = (mudancas.get("concluida") is True and not alvo.concluida)
        for k, v in mudancas.items():
            if k not in _CAMPOS_TAREFA:
                continue
            if k == "min":
                alvo.min = int(v) if v is not None else None
            else:
                setattr(alvo, k, v)
        self._salvar_entradas(entradas)
        if concluir:
            # tudo que é concluído vira uma linha timestampada no diário "Acabei de
            # fazer" — é o log que a gente vai sistematizar depois. O XP vem daqui
            # uma vez só (a auto-entrada não usa `anotar`, que também daria XP).
            energia = _ENERGIAS.get((alvo.energia or "").strip().lower(), "média")
            self._inserir_diario(alvo.titulo, energia, self.agora())
            self._ganhar_xp(xp_por_energia(alvo.energia))
        return alvo

    # ---- diário (o que você acabou de fazer, fora da lista) ----
    def _inserir_diario(self, texto, energia, agora):
        """Grava uma linha no diário. Não dá XP — quem chama decide isso."""
        a = Anotacao(dia=agora.date().isoformat(), hora=agora.strftime("%H:%M"),
                     texto=texto, energia=energia)
        entradas = inserir(parse_diario(ler_texto(self.vault.diario_md)), a)
        escrever_texto_atomico(self.vault.diario_md, serializar_diario(entradas))
        return a

    def anotar(self, texto, energia=None):
        texto = limpar_texto(texto)
        if not texto:
            raise ValueError("texto vazio")
        energia = _ENERGIAS.get((energia or "").strip().lower(), "média")
        a = self._inserir_diario(texto, energia, self.agora())
        self._ganhar_xp(xp_por_energia(energia))
        return a

    def listar_anotacoes(self, dia=None):
        entradas = parse_diario(ler_texto(self.vault.diario_md))
        if dia == "tudo":
            return todas_anotacoes(entradas)
        return anotacoes_do_dia(entradas, dia or self.hoje().isoformat())

    # ---- financeiro (recebimentos, contas, gastos) ----
    def _ler_financeiro(self):
        entradas = parse_financeiro(ler_texto(self.vault.financeiro_md))
        if garantir_ids_fin(entradas):
            escrever_texto_atomico(self.vault.financeiro_md,
                                   serializar_financeiro(entradas))
        return entradas

    def _salvar_financeiro(self, entradas):
        escrever_texto_atomico(self.vault.financeiro_md,
                               serializar_financeiro(entradas))

    def listar_financeiro(self):
        entradas = self._ler_financeiro()
        return {
            "recebimentos": [e for e in entradas if isinstance(e, Entrada)],
            "fixos": [e for e in entradas if isinstance(e, Fixo)],
            "contas": [e for e in entradas if isinstance(e, Conta)],
            "gastos": [e for e in entradas if isinstance(e, Gasto)],
            "resumo": resumo(entradas),
        }

    def _marcar(self, tipo, id, mudancas, campos):
        entradas = self._ler_financeiro()
        alvo = next((e for e in entradas
                     if isinstance(e, tipo) and e.id == id), None)
        if alvo is None:
            return None
        ts = self.agora().isoformat(timespec="minutes")
        for campo in campos:
            if campo in mudancas:
                # bool -> grava o horário de quando marquei; desmarcar limpa o campo
                setattr(alvo, campo, ts if mudancas[campo] else None)
        self._salvar_financeiro(entradas)
        return alvo

    def editar_entrada(self, id, mudancas):
        return self._marcar(Entrada, id, mudancas, ("pago",))

    def editar_conta(self, id, mudancas):
        return self._marcar(Conta, id, mudancas, ("pago",))

    def editar_fixo(self, id, mudancas):
        return self._marcar(Fixo, id, mudancas, ("pago",))

    def _gravar_mes(self, entradas, nome, valor):
        """Grava um número na seção `## Mês`. Cria a seção e a linha se faltarem."""
        linha = linha_mes(entradas, nome)
        if linha is None:
            linha = Mes(nome=nome)
            idx = indice_secao(entradas, "mês")
            if idx is None:
                idx = indice_secao(entradas, "mes")
            if idx is None:
                entradas += ["", "## Mês", linha]
            else:
                entradas.insert(idx + 1, linha)
        # o .md é lido por humano: 1500, não 1500.0
        n = num(valor)
        linha.valor = str(int(n)) if n == int(n) else str(round(n, 2))

    def definir_guardado(self, valor):
        """Grava quanto foi guardado no mês (a reserva)."""
        entradas = self._ler_financeiro()
        self._gravar_mes(entradas, "guardado", valor)
        self._salvar_financeiro(entradas)
        return resumo(entradas)

    # ---- metas (companheiros de poupança na Agora: a reserva de fábrica) ----
    def estado_metas(self):
        """As metas com sprite e nome do Pokémon prontos pra tela."""
        ms = metas(self._ler_financeiro())
        for m in ms:
            m["sprite"] = self.cliente.sprite(m["pokemon"])
            m["nome"] = nome_bonito(m["pokemon"])
        return ms

    def definir_guardado_meta(self, chave, valor):
        """Grava (seta) o guardado de uma meta pela chave — caminho de correção. O
        acúmulo do dia a dia é depósito (`depositar_meta`), não isto."""
        nome = LINHA_META.get(chave)
        if nome is None:
            raise ValueError("meta desconhecida")
        entradas = self._ler_financeiro()
        self._gravar_mes(entradas, nome, valor)
        self._salvar_financeiro(entradas)
        return self.estado_metas()

    def depositar_meta(self, chave, valor):
        """Soma um depósito ao guardado da meta. O número que você digita é uma
        quantia que acabou de guardar — só empurra pra cima, nunca reescreve o
        total. Corrigir pra menos é editar o `financeiro.md` na mão, de propósito."""
        nome = LINHA_META.get(chave)
        if nome is None:
            raise ValueError("meta desconhecida")
        entradas = self._ler_financeiro()
        atual = linha_mes(entradas, nome)
        base = num(atual.valor) if atual else 0.0
        self._gravar_mes(entradas, nome, base + num(valor))
        self._salvar_financeiro(entradas)
        return self.estado_metas()

    def adicionar_gasto(self, dados):
        local = (dados.get("local") or "").strip()
        if not local:
            raise ValueError("local vazio")
        entradas = self._ler_financeiro()
        valor = dados.get("valor")
        g = Gasto(local=local, data=self.hoje().isoformat(),
                  valor=str(valor) if valor not in (None, "") else None)
        idx = indice_secao(entradas, "gastos")
        if idx is None:
            entradas += ["", "## Gastos", g]
        else:
            entradas.insert(idx + 1, g)   # logo abaixo do cabeçalho: mais recente no topo
        garantir_ids_fin(entradas)
        self._salvar_financeiro(entradas)
        return g

    # ---- inbox ----
    def contar_inbox(self):
        """Quantas linhas o braindump tem esperando triagem."""
        texto = ler_texto(self.vault.inbox_md)
        corpo = texto.split(_MARCADOR_INBOX, 1)[1] if _MARCADOR_INBOX in texto else ""
        return sum(1 for linha in corpo.splitlines() if linha.strip())

    def listar_inbox(self):
        """As linhas cruas esperando triagem."""
        texto = ler_texto(self.vault.inbox_md)
        corpo = texto.split(_MARCADOR_INBOX, 1)[1] if _MARCADOR_INBOX in texto else ""
        return [l.strip().lstrip("-").strip()
                for l in corpo.splitlines() if l.strip()]

    def despejar_inbox(self, texto):
        """Captura rápida: uma linha direto no fim do inbox, sem triagem.

        É o caminho de menor atrito da tela "Agora" — o pensamento sai da cabeça
        e cai no braindump. Quem organiza depois é a `/triagem`.
        """
        texto = limpar_texto(texto or "")
        if not texto:
            raise ValueError("texto é obrigatório")
        atual = ler_texto(self.vault.inbox_md)
        if _MARCADOR_INBOX not in atual:
            atual = (atual.rstrip("\n") + "\n\n---\n\n## Pra triar\n\n"
                     + _MARCADOR_INBOX + "\n")
        corpo = atual.rstrip("\n") + f"\n- {texto}\n"
        escrever_texto_atomico(self.vault.inbox_md, corpo)
        return {"texto": texto, "pendentes": self.contar_inbox()}

    # ---- dieta (refeições somente leitura + lista de compras) ----
    def _ler_dieta(self):
        entradas = parse_dieta(ler_texto(self.vault.dieta_md))
        if garantir_ids_dieta(entradas):
            escrever_texto_atomico(self.vault.dieta_md, serializar_dieta(entradas))
        return entradas

    def listar_dieta(self):
        entradas = self._ler_dieta()
        texto = ler_texto(self.vault.dieta_md)
        return {
            "refeicoes": refeicoes_de(texto),
            "compras": [e for e in entradas if isinstance(e, Compra)],
            "corpo": corpo_de(texto),
            "notas": self.listar_notas_dieta(),
        }

    def despejar_dieta(self, texto):
        """Inbox só da dieta: "comprei o nhoque", "será que troco o kibe?".

        Fica em `## Inbox da dieta`, no topo do `dieta.md`. Nenhum parser lê essa
        seção (as compras só valem sob `## Compras`), então é texto livre seguro.
        """
        texto = limpar_texto(texto or "")
        if not texto:
            raise ValueError("texto é obrigatório")
        linhas = ler_texto(self.vault.dieta_md).splitlines()
        linha = f"- {self.hoje().isoformat()} · {texto}"
        if _SECAO_INBOX_DIETA in linhas:
            # mais recente em cima
            linhas.insert(linhas.index(_SECAO_INBOX_DIETA) + 1, linha)
        else:
            # nasce antes da primeira seção do arquivo (topo, logo após o título)
            corte = next((i for i, l in enumerate(linhas)
                          if l.startswith("## ")), len(linhas))
            linhas[corte:corte] = [_SECAO_INBOX_DIETA, linha, ""]
        escrever_texto_atomico(self.vault.dieta_md, "\n".join(linhas) + "\n")
        return {"texto": texto, "notas": self.listar_notas_dieta()}

    def listar_notas_dieta(self):
        texto = ler_texto(self.vault.dieta_md)
        if _SECAO_INBOX_DIETA not in texto:
            return []
        corpo = texto.split(_SECAO_INBOX_DIETA, 1)[1]
        corpo = corpo.split("\n## ", 1)[0]
        return [l.strip()[2:].strip() for l in corpo.splitlines()
                if l.strip().startswith("- ")]

    def marcar_compra(self, id, comprado):
        entradas = self._ler_dieta()
        alvo = next((e for e in entradas
                     if isinstance(e, Compra) and e.id == id), None)
        if alvo is None:
            return None
        alvo.comprado = (self.agora().isoformat(timespec="minutes")
                         if comprado else None)
        escrever_texto_atomico(self.vault.dieta_md, serializar_dieta(entradas))
        return alvo

    # ---- objetivos (leitura: long prazo + o que está em andamento) ----
    def listar_objetivos(self):
        return montar_objetivos(ler_texto(self.vault.objetivos_md),
                                ler_texto(self.vault.tarefas_md))

    # ---- pokemon ----
    def _favoritos(self):
        favs = []
        for linha in ler_texto(self.vault.pokemons_md).splitlines():
            linha = linha.strip()
            if linha.startswith("- "):
                favs.append(linha[2:].strip())
        return favs

    def _resolver_cadeia(self, especie):
        return self.cliente.cadeia_evolucao(especie, self.rng)

    def _carregar_progresso(self):
        bruto = ler_texto(self.vault.progresso_json)
        if not bruto.strip():
            # o primeiro companheiro é o topo de pokemons.md (bulbasaur), não um
            # sorteio: começar sempre no mesmo cria vínculo. O sorteio só entra
            # depois, quando você conclui uma cadeia inteira.
            pool = self._favoritos()
            inicial = pool[0] if pool else "bulbasaur"
            prog = Progresso(pokemon_atual=inicial,
                             cadeia=self._resolver_cadeia(inicial))
            self._salvar_progresso(prog)
            return prog
        d = json.loads(bruto)
        prog = Progresso(
            pokemon_atual=d["pokemon_atual"],
            xp=d.get("xp", 0),
            concluidos=d.get("concluidos", []),
            cadeia=d.get("cadeia", []),
        )
        if not prog.cadeia:  # migração de progresso.json anterior a esta revisão
            prog.cadeia = self._resolver_cadeia(prog.pokemon_atual)
            self._salvar_progresso(prog)
        return prog

    def _salvar_progresso(self, prog):
        escrever_texto_atomico(
            self.vault.progresso_json,
            json.dumps({
                "pokemon_atual": prog.pokemon_atual,
                "xp": prog.xp,
                "concluidos": prog.concluidos,
                "cadeia": prog.cadeia,
            }, ensure_ascii=False, indent=2) + "\n",
        )

    def _ganhar_xp(self, ganho):
        prog = self._carregar_progresso()
        novo = aplicar_xp(prog, ganho, self._favoritos(),
                          self._resolver_cadeia, self.rng)
        self._salvar_progresso(novo)
        return novo

    def estado_pokemon(self):
        prog = self._carregar_progresso()
        try:
            estagio = prog.cadeia.index(prog.pokemon_atual)
        except ValueError:
            estagio = 0
        return {
            "nome": nome_bonito(prog.pokemon_atual),
            "sprite": self.cliente.sprite(prog.pokemon_atual),
            "xp": prog.xp,
            "xp_para_evoluir": limiar_do_estagio(estagio),
            "estagio": estagio,
        }
