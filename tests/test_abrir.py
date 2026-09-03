import abrir


def test_esperar_cair_true_quando_porta_livre(monkeypatch):
    monkeypatch.setattr(abrir, "no_ar", lambda: False)
    assert abrir.esperar_cair(1.0) is True


def test_esperar_cair_false_no_timeout(monkeypatch):
    monkeypatch.setattr(abrir, "no_ar", lambda: True)
    assert abrir.esperar_cair(0.05) is False


def test_reiniciar_espera_cair_depois_sobe_depois_espera_subir(monkeypatch):
    ordem = []
    monkeypatch.setattr(abrir, "esperar_cair", lambda *a, **k: (ordem.append("cair"), True)[1])
    monkeypatch.setattr(abrir, "subir_servidor", lambda: ordem.append("subir"))
    monkeypatch.setattr(abrir, "esperar", lambda *a, **k: (ordem.append("subiu"), True)[1])
    assert abrir.reiniciar() == 0
    assert ordem == ["cair", "subir", "subiu"]


def test_reiniciar_aborta_se_velho_nao_cai(monkeypatch):
    avisos = []
    monkeypatch.setattr(abrir, "esperar_cair", lambda *a, **k: False)
    monkeypatch.setattr(abrir, "subir_servidor", lambda: avisos.append("subiu"))
    monkeypatch.setattr(abrir, "avisar", lambda msg: avisos.append(msg))
    assert abrir.reiniciar() == 1
    assert "subiu" not in avisos   # não tenta subir se o velho não caiu
