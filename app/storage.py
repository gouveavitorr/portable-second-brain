import os
import shutil
import sys
import tempfile
from pathlib import Path


def _raiz_projeto() -> Path:
    return Path(__file__).resolve().parent.parent


def caminho_do_vault() -> Path:
    """Onde o vault mora. Em dev é a pasta `second_brain/` do projeto; empacotado
    (PyInstaller) vai pra `Documentos/SecondBrain`, um lugar fixo e por-usuário, não
    o cwd imprevisível do exe. `SECOND_BRAIN_VAULT` força um caminho (útil pra teste)."""
    override = os.environ.get("SECOND_BRAIN_VAULT")
    if override:
        return Path(override)
    if getattr(sys, "frozen", False):
        return Path.home() / "Documents" / "SecondBrain"
    return _raiz_projeto() / "second_brain"


def _dir_semente() -> Path:
    """A semente do vault que vai junto do app: os `.md` de exemplo. Empacotado,
    os dados ficam em `sys._MEIPASS`; em dev, na própria pasta do projeto."""
    base = getattr(sys, "_MEIPASS", None)
    raiz = Path(base) if base else _raiz_projeto()
    return raiz / "second_brain"


def preparar_vault() -> "Vault":
    """Resolve o caminho do vault e, se ele ainda não foi semeado, copia a semente
    pra lá. Devolve um `Vault` pronto pra uso.

    O gatilho é "falta o `tarefas.md`", não "a pasta não existe": a pasta pode já
    ter sido criada por outra coisa (um log, um marcador) sem o conteúdo — e mesmo
    assim precisa da semente. `dirs_exist_ok` deixa mesclar sem apagar o que houver.
    """
    destino = caminho_do_vault()
    semente = _dir_semente()
    precisa_semear = not (destino / "tarefas.md").exists()
    if (precisa_semear and semente.exists()
            and semente.resolve() != destino.resolve()):
        shutil.copytree(
            semente, destino, dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(
                ".cache", "progresso.json", "estado.md", ".primeira-vez"),
        )
    v = Vault(destino)
    v.garantir()
    return v


def ler_texto(caminho: Path) -> str:
    p = Path(caminho)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def escrever_texto_atomico(caminho: Path, conteudo: str) -> None:
    p = Path(caminho)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=".tmp-", suffix=p.suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(conteudo)
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


class Vault:
    def __init__(self, base: Path):
        self.base = Path(base)

    @property
    def tarefas_md(self) -> Path:
        return self.base / "tarefas.md"

    @property
    def pokemons_md(self) -> Path:
        return self.base / "pokemons.md"

    @property
    def diario_md(self) -> Path:
        return self.base / "diario.md"

    @property
    def financeiro_md(self) -> Path:
        return self.base / "financeiro.md"

    @property
    def dieta_md(self) -> Path:
        return self.base / "dieta.md"

    @property
    def objetivos_md(self) -> Path:
        return self.base / "objetivos.md"

    @property
    def inbox_md(self) -> Path:
        return self.base / "inbox.md"

    @property
    def progresso_json(self) -> Path:
        return self.base / "progresso.json"

    @property
    def cache_dir(self) -> Path:
        return self.base / ".cache" / "pokeapi"

    def garantir(self) -> None:
        self.base.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
