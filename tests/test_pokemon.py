import random
from app.pokemon import (
    LIMIAR_XP,
    xp_por_energia,
    limiar_do_estagio,
    nome_bonito,
    Progresso,
    sortear_proximo,
    aplicar_xp,
)

CHAR = ["charmander", "charmeleon", "charizard"]


def _resolver(nome):
    tabela = {
        "eevee": ["eevee", "sylveon"],
        "pichu": ["pichu", "pikachu", "raichu"],
        "charmander": CHAR,
    }
    return tabela.get(nome, [nome])


def test_xp_por_energia():
    assert xp_por_energia("leve") == 10
    assert xp_por_energia(None) == 15
    assert xp_por_energia("media") == 15
    assert xp_por_energia("pesada") == 25


def test_limiar_por_estagio():
    assert limiar_do_estagio(0) == LIMIAR_XP == 100
    assert limiar_do_estagio(1) == 200
    assert limiar_do_estagio(2) == 300
    assert limiar_do_estagio(7) == 300   # cadeia maior repete o último
    assert limiar_do_estagio(-1) == 100


def test_nome_bonito():
    assert nome_bonito("charmander") == "Charmander"
    assert nome_bonito("nidoran-m") == "Nidoran♂"
    assert nome_bonito("nidoran-f") == "Nidoran♀"
    assert nome_bonito("mr-mime") == "Mr. Mime"
    assert nome_bonito("farfetchd") == "Farfetch'd"
    assert nome_bonito("porygon-z") == "Porygon-Z"
    assert nome_bonito("HO-OH") == "Ho-Oh"
    assert nome_bonito("tapu-koko") == "Tapu Koko"   # slug sem regra: vira nome
    assert nome_bonito(None) == ""


def test_aplicar_xp_sem_evoluir():
    prog = Progresso(pokemon_atual="charmander", xp=60, cadeia=CHAR)
    novo = aplicar_xp(prog, 25, ["charmander"], _resolver, random.Random(1))
    assert novo.xp == 85
    assert novo.pokemon_atual == "charmander"
    assert novo.cadeia == CHAR
    assert prog.xp == 60  # imutabilidade


def test_evolucao_carrega_excedente():
    prog = Progresso(pokemon_atual="charmander", xp=90, cadeia=CHAR)
    novo = aplicar_xp(prog, 20, ["charmander"], _resolver, random.Random(1))
    assert novo.pokemon_atual == "charmeleon"
    assert novo.xp == 10
    assert novo.cadeia == CHAR


def test_evolucoes_multiplas_de_uma_vez():
    prog = Progresso(pokemon_atual="charmander", xp=0, cadeia=CHAR)
    # 100 para a primeira evolução + 200 para a segunda, sobram 50
    novo = aplicar_xp(prog, 350, ["charmander", "eevee"], _resolver, random.Random(1))
    assert novo.pokemon_atual == "charizard"
    assert novo.xp == 50


def test_segundo_estagio_custa_o_dobro():
    prog = Progresso(pokemon_atual="charmeleon", xp=150, cadeia=CHAR)
    quase = aplicar_xp(prog, 40, ["charmeleon"], _resolver, random.Random(1))
    assert quase.pokemon_atual == "charmeleon" and quase.xp == 190
    passou = aplicar_xp(prog, 60, ["charmeleon"], _resolver, random.Random(1))
    assert passou.pokemon_atual == "charizard" and passou.xp == 10


def test_fim_da_cadeia_conclui_sorteia_e_resolve_nova_cadeia():
    prog = Progresso(pokemon_atual="charizard", xp=290, cadeia=CHAR)
    # pool com um só candidato: torna o sorteio determinístico
    novo = aplicar_xp(prog, 20, ["eevee"], _resolver, random.Random(1))
    assert "charizard" in novo.concluidos
    assert novo.pokemon_atual == "eevee"
    assert novo.cadeia == ["eevee", "sylveon"]
    assert novo.xp == 10


def test_pokemon_sem_evolucao_conclui_no_limiar():
    prog = Progresso(pokemon_atual="mew", xp=90, cadeia=["mew"])
    novo = aplicar_xp(prog, 20, ["mew", "eevee"], _resolver, random.Random(1))
    assert "mew" in novo.concluidos
    assert novo.pokemon_atual == "eevee"
    assert novo.cadeia == ["eevee", "sylveon"]


def test_cadeia_comecando_na_base_de_outra_geracao():
    prog = Progresso(pokemon_atual="pichu", xp=90, cadeia=["pichu", "pikachu", "raichu"])
    novo = aplicar_xp(prog, 20, ["pichu"], _resolver, random.Random(1))
    assert novo.pokemon_atual == "pikachu"


def test_sortear_prefere_nao_concluidos():
    esc, conc = sortear_proximo(["a", "b", "c"], concluidos=["a", "b"], rng=random.Random(0))
    assert esc == "c"
    assert conc == ["a", "b"]


def test_sortear_todos_concluidos_reseta():
    esc, conc = sortear_proximo(["a", "b"], concluidos=["a", "b"], rng=random.Random(0))
    assert esc in ("a", "b")
    assert conc == []


def test_invariante_xp_nunca_diminui_sem_evolucao():
    prog = Progresso(pokemon_atual="charmander", xp=50, cadeia=CHAR)
    novo = aplicar_xp(prog, -999, ["charmander"], _resolver, random.Random(1))
    assert novo.xp == 50
    assert novo.pokemon_atual == "charmander"
