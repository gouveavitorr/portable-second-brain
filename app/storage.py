import os
import tempfile
from pathlib import Path


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
