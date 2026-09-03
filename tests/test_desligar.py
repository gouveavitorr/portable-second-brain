import random
from fastapi.testclient import TestClient
from app.storage import Vault
from app.pokemon import ClientePokeAPI
from app.servico import Servico
from app import main
from app.main import criar_app


def _client(tmp_path):
    v = Vault(tmp_path)
    v.garantir()
    v.pokemons_md.write_text("- charmander\n", encoding="utf-8")
    servico = Servico(v, ClientePokeAPI(v.cache_dir), rng=random.Random(1))
    return TestClient(criar_app(servico))


def test_desligar_dispara_encerramento(tmp_path, monkeypatch):
    chamado = {}
    monkeypatch.setattr(main, "_encerrar_em_breve",
                        lambda *a, **k: chamado.setdefault("sim", True))
    c = _client(tmp_path)
    r = c.post("/api/desligar")
    assert r.status_code == 200
    assert r.json() == {"desligando": True}
    assert chamado.get("sim")


def test_reiniciar_dispara_ajudante_antes_de_encerrar(tmp_path, monkeypatch):
    # A ordem é o que importa: se o servidor cai antes de o ajudante subir, ninguém
    # sobe o substituto e a porta fica órfã.
    ordem = []
    monkeypatch.setattr(main, "_disparar_reiniciar", lambda: ordem.append("ajudante"))
    monkeypatch.setattr(main, "_encerrar_em_breve", lambda *a, **k: ordem.append("encerrar"))
    c = _client(tmp_path)
    r = c.post("/api/reiniciar")
    assert r.status_code == 200
    assert r.json() == {"reiniciando": True}
    assert ordem == ["ajudante", "encerrar"]
