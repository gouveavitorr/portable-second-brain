from datetime import datetime
from app.calendario import Evento, ja_passou


def _ev(inicio, fim, dia_inteiro=False):
    return Evento(titulo="x",
                  inicio=datetime(2026, 7, 15, *inicio),
                  fim=datetime(2026, 7, 15, *fim),
                  dia_inteiro=dia_inteiro)


def test_evento_terminado_passou():
    assert ja_passou(_ev((8, 0), (8, 45)), datetime(2026, 7, 15, 19, 0))


def test_evento_futuro_nao_passou():
    assert not ja_passou(_ev((20, 30), (21, 30)), datetime(2026, 7, 15, 19, 0))


def test_evento_em_curso_nao_passou():
    assert not ja_passou(_ev((18, 15), (19, 15)), datetime(2026, 7, 15, 19, 0))


def test_no_instante_do_fim_ja_passou():
    assert ja_passou(_ev((18, 15), (19, 15)), datetime(2026, 7, 15, 19, 15))


def test_dia_inteiro_nunca_passa():
    assert not ja_passou(_ev((0, 0), (8, 0), dia_inteiro=True),
                         datetime(2026, 7, 15, 19, 0))
