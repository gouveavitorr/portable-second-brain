from datetime import datetime, date
from app.calendario import (
    Evento,
    parse_eventos,
    janela_livre,
    evento_atual,
)


def _dt(h, m=0):
    return datetime(2026, 7, 14, h, m)


def _bruto(titulo, inicio, fim, dia_inteiro=False, status=None):
    """Imita a forma que a API do Google Calendar devolve."""
    if dia_inteiro:
        tempo = {"start": {"date": "2026-07-14"}, "end": {"date": "2026-07-15"}}
    else:
        tempo = {"start": {"dateTime": inicio}, "end": {"dateTime": fim}}
    item = {"summary": titulo, **tempo}
    if status:
        item["attendees"] = [{"self": True, "responseStatus": status}]
    return item


def test_parse_evento_normal():
    itens = [_bruto("Reunião", "2026-07-14T14:30:00-03:00", "2026-07-14T15:30:00-03:00")]
    (e,) = parse_eventos(itens)
    assert isinstance(e, Evento)
    assert e.titulo == "Reunião"
    assert e.inicio.hour == 14 and e.inicio.minute == 30
    assert e.fim.hour == 15
    assert e.dia_inteiro is False


def test_parse_evento_dia_inteiro():
    (e,) = parse_eventos([_bruto("Feriado", None, None, dia_inteiro=True)])
    assert e.dia_inteiro is True
    assert e.titulo == "Feriado"


def test_parse_evento_sem_titulo():
    itens = [{"start": {"dateTime": "2026-07-14T14:00:00-03:00"},
              "end": {"dateTime": "2026-07-14T15:00:00-03:00"}}]
    (e,) = parse_eventos(itens)
    assert e.titulo == "(sem título)"


def test_parse_ignora_evento_recusado():
    itens = [
        _bruto("Recusada", "2026-07-14T14:00:00-03:00", "2026-07-14T15:00:00-03:00",
               status="declined"),
        _bruto("Aceita", "2026-07-14T16:00:00-03:00", "2026-07-14T17:00:00-03:00",
               status="accepted"),
    ]
    eventos = parse_eventos(itens)
    assert [e.titulo for e in eventos] == ["Aceita"]


def test_janela_livre_ate_proximo_evento():
    eventos = [Evento("Reunião", _dt(14, 30), _dt(15, 30))]
    assert janela_livre(eventos, agora=_dt(14, 5)) == 25


def test_janela_livre_sem_eventos_e_none():
    assert janela_livre([], agora=_dt(9)) is None


def test_janela_livre_ignora_eventos_ja_passados():
    eventos = [Evento("Passada", _dt(9), _dt(10)),
               Evento("Futura", _dt(16), _dt(17))]
    assert janela_livre(eventos, agora=_dt(15, 30)) == 30


def test_janela_livre_ignora_dia_inteiro():
    eventos = [Evento("Feriado", _dt(0), _dt(23, 59), dia_inteiro=True)]
    assert janela_livre(eventos, agora=_dt(9)) is None


def test_janela_livre_zero_durante_evento():
    eventos = [Evento("Reunião", _dt(14), _dt(15))]
    assert janela_livre(eventos, agora=_dt(14, 30)) == 0


def test_janela_livre_none_quando_so_restam_passados():
    eventos = [Evento("Passada", _dt(9), _dt(10))]
    assert janela_livre(eventos, agora=_dt(11)) is None


def test_evento_atual_dentro():
    eventos = [Evento("Reunião", _dt(14), _dt(15))]
    e = evento_atual(eventos, agora=_dt(14, 30))
    assert e.titulo == "Reunião"


def test_evento_atual_fora_e_none():
    eventos = [Evento("Reunião", _dt(14), _dt(15))]
    assert evento_atual(eventos, agora=_dt(13)) is None


def test_evento_atual_ignora_dia_inteiro():
    eventos = [Evento("Feriado", _dt(0), _dt(23, 59), dia_inteiro=True)]
    assert evento_atual(eventos, agora=_dt(12)) is None
