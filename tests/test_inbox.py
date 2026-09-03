import random
from datetime import datetime

from fastapi.testclient import TestClient

from app.storage import Vault
from app.pokemon import ClientePokeAPI
from app.servico import Servico
from app.main import criar_app
from tests.test_api_diario import _fetch_fake

AGORA = datetime(2026, 7, 20, 10, 0)

INBOX = """# 📥 Inbox

Prosa de instrução que não conta como item.

## Pra triar

<!-- escreve abaixo desta linha -->

preciso comprar pão
preciso ligar pro dentista
"""

VAZIO = """# 📥 Inbox

## Pra triar

<!-- escreve abaixo desta linha -->
"""


def _servico(tmp_path, inbox=INBOX):
    v = Vault(tmp_path)
    v.garantir()
    v.pokemons_md.write_text("- charmander\n", encoding="utf-8")
    v.inbox_md.write_text(inbox, encoding="utf-8")
    s = Servico(v, ClientePokeAPI(v.cache_dir, fetch=_fetch_fake),
                rng=random.Random(1), agora=lambda: AGORA)
    return s, v


def test_conta_so_o_que_esta_abaixo_do_marcador(tmp_path):
    s, _ = _servico(tmp_path)
    assert s.contar_inbox() == 2       # a prosa de cima não conta


def test_inbox_vazio_conta_zero(tmp_path):
    s, _ = _servico(tmp_path, inbox=VAZIO)
    assert s.contar_inbox() == 0


def test_api_inbox(tmp_path):
    s, _ = _servico(tmp_path)
    c = TestClient(criar_app(s))
    assert c.get("/api/inbox").json() == {"pendentes": 2}
