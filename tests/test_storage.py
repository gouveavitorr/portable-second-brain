from pathlib import Path
from app.storage import escrever_texto_atomico, ler_texto, Vault


def test_ler_texto_arquivo_inexistente_retorna_vazio(tmp_path):
    assert ler_texto(tmp_path / "nao_existe.md") == ""


def test_escrever_e_ler_round_trip(tmp_path):
    alvo = tmp_path / "sub" / "a.md"
    alvo.parent.mkdir()
    escrever_texto_atomico(alvo, "olá\nmundo\n")
    assert ler_texto(alvo) == "olá\nmundo\n"


def test_escrever_atomico_nao_deixa_temp(tmp_path):
    alvo = tmp_path / "a.md"
    escrever_texto_atomico(alvo, "x")
    filhos = [p.name for p in tmp_path.iterdir()]
    assert filhos == ["a.md"]


def test_vault_expondo_caminhos(tmp_path):
    v = Vault(tmp_path)
    assert v.tarefas_md == tmp_path / "tarefas.md"
    assert v.pokemons_md == tmp_path / "pokemons.md"
    assert v.progresso_json == tmp_path / "progresso.json"
    assert v.cache_dir == tmp_path / ".cache" / "pokeapi"


def test_vault_garantir_cria_dirs(tmp_path):
    base = tmp_path / "second_brain"
    v = Vault(base)
    v.garantir()
    assert base.is_dir()
    assert v.cache_dir.is_dir()
