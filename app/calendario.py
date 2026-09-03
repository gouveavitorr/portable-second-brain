"""Cálculo da janela livre a partir de eventos do dia.

Tudo aqui é puro e offline (testável sem rede). A versão portátil não fala com
nenhum calendário externo: `Servico` recebe `calendario=None` e o app funciona
sem consciência de tempo. Estas funções continuam aqui porque o motor da tela
"Agora" usa `janela_livre` — e porque, se um dia alguém quiser plugar uma fonte
de eventos local, o formato (`Evento`) e os cálculos já estão prontos.
"""
from dataclasses import dataclass
from datetime import datetime, date


@dataclass
class Evento:
    titulo: str
    inicio: datetime
    fim: datetime
    dia_inteiro: bool = False


def _sem_tz(dt: datetime) -> datetime:
    """Descarta o fuso: o app é local, tudo acontece no horário do usuário."""
    return dt.replace(tzinfo=None)


def parse_eventos(itens) -> list:
    eventos = []
    for item in itens:
        if _recusado(item):
            continue
        inicio_bruto = item.get("start", {})
        fim_bruto = item.get("end", {})
        titulo = item.get("summary") or "(sem título)"
        if "date" in inicio_bruto:  # evento de dia inteiro
            dia = date.fromisoformat(inicio_bruto["date"])
            eventos.append(Evento(
                titulo=titulo,
                inicio=datetime.combine(dia, datetime.min.time()),
                fim=datetime.combine(dia, datetime.max.time()),
                dia_inteiro=True,
            ))
            continue
        if "dateTime" not in inicio_bruto:
            continue
        eventos.append(Evento(
            titulo=titulo,
            inicio=_sem_tz(datetime.fromisoformat(inicio_bruto["dateTime"])),
            fim=_sem_tz(datetime.fromisoformat(fim_bruto["dateTime"])),
        ))
    return eventos


def _recusado(item) -> bool:
    for pessoa in item.get("attendees", []):
        if pessoa.get("self") and pessoa.get("responseStatus") == "declined":
            return True
    return False


def _agendados(eventos):
    """Só os eventos que realmente ocupam um horário."""
    return [e for e in eventos if not e.dia_inteiro]


def evento_atual(eventos, agora: datetime):
    for e in _agendados(eventos):
        if e.inicio <= agora < e.fim:
            return e
    return None


def ja_passou(evento, agora: datetime) -> bool:
    """Evento que já terminou. Dia inteiro nunca passa: ele vale o dia todo."""
    if evento.dia_inteiro:
        return False
    return evento.fim <= agora


def janela_livre(eventos, agora: datetime):
    """Minutos livres até o próximo compromisso.

    Devolve 0 se você está dentro de um evento agora, e None se não há mais
    nada marcado hoje (janela ilimitada).
    """
    if evento_atual(eventos, agora):
        return 0
    futuros = [e for e in _agendados(eventos) if e.inicio > agora]
    if not futuros:
        return None
    proximo = min(futuros, key=lambda e: e.inicio)
    return int((proximo.inicio - agora).total_seconds() // 60)
