"""Sobe o servidor (se já não estiver no ar) e abre a tela "Agora" no navegador.

Pensado pra ser chamado com um clique — pelo `iniciar.bat` em dev, ou pelo próprio
`.exe` quando empacotado (PyInstaller). Se o app já estiver rodando, não sobe um segundo:
só abre a aba.

Três modos:
- normal: escolhe uma porta livre, sobe o servidor (escondido) e abre o navegador.
- `--servir`: roda o uvicorn **in-process**. É este o processo do servidor — funciona
  igual rodando de `python` ou de dentro do exe, sem depender de um `python -m uvicorn`
  externo. Chamado por `subir_servidor()`.
- `--reiniciar`: usado pelo endpoint /api/reiniciar. Espera o servidor velho cair, sobe
  um novo (escondido) na mesma porta e sai.

Empacotado (`sys.frozen`), `subir_servidor` e o reinício re-executam o **próprio exe**
com o flag — `comando_base()` cuida disso. A porta escolhida é persistida em
`.servidor.port` pra o reinício e o navegador acharem o mesmo endereço.
"""
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

PORTA_PADRAO = 8000
RAIZ = Path(__file__).resolve().parent


def _dir_estado() -> Path:
    """Onde guardar o log e a porta: um lugar escrevível. Empacotado, o cwd do exe
    pode ser read-only (Program Files), então cai junto do vault, por-usuário."""
    if getattr(sys, "frozen", False):
        from app.storage import caminho_do_vault
        d = caminho_do_vault()
        d.mkdir(parents=True, exist_ok=True)
        return d
    return RAIZ


LOG = _dir_estado() / ".servidor.log"
ARQ_PORTA = _dir_estado() / ".servidor.port"


def comando_base() -> list:
    """Como re-executar 'a mim mesmo': o próprio exe quando empacotado, senão o
    python + este script. Quem monta os comandos --servir e --reiniciar."""
    if getattr(sys, "frozen", False):
        return [sys.executable]
    return [python_de_console(), str(RAIZ / "abrir.py")]


def python_de_console() -> str:
    """O interpretador com console, mesmo se este script rodar sob pythonw.

    pythonw deixa sys.stdout = None; o uvicorn morre (rc=1) ao tentar logar.
    """
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe":
        console = exe.with_name("python.exe")
        if console.exists():
            return str(console)
    return str(exe)


# ---- porta ----

def _porta_livre(porta: int) -> bool:
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", porta))
            return True
        except OSError:
            return False


def _porta_efemera() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def porta_persistida():
    try:
        return int(ARQ_PORTA.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def escolher_porta() -> int:
    """Fixa uma porta pra esta execução: a 8000 se estiver livre, senão uma
    efêmera qualquer. Persiste pra o reinício e o navegador usarem a mesma."""
    porta = PORTA_PADRAO if _porta_livre(PORTA_PADRAO) else _porta_efemera()
    ARQ_PORTA.write_text(str(porta), encoding="utf-8")
    return porta


def porta_ativa() -> int:
    return porta_persistida() or PORTA_PADRAO


def url() -> str:
    return f"http://127.0.0.1:{porta_ativa()}"


def porta_em_uso(porta: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", porta)) == 0


def no_ar() -> bool:
    """Já tem servidor nosso no ar? Só se a porta persistida está ocupada."""
    p = porta_persistida()
    return p is not None and porta_em_uso(p)


# ---- subir / servir ----

def servir() -> None:
    """O processo do servidor: uvicorn in-process, na porta persistida."""
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=porta_ativa(),
                log_level="info")


def subir_servidor() -> None:
    # Sem janela de console (CREATE_NO_WINDOW); o log do uvicorn vai pra
    # .servidor.log, que é o indicador de "por que não subiu".
    sem_janela = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    log = open(LOG, "a", buffering=1, encoding="utf-8")
    subprocess.Popen(
        comando_base() + ["--servir"],
        cwd=str(RAIZ),
        creationflags=sem_janela,
        stdout=log,
        stderr=subprocess.STDOUT,
    )


def esperar(segundos: float = 30.0) -> bool:
    """Espera a porta subir — o servidor novo está no ar."""
    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        if no_ar():
            return True
        time.sleep(0.4)
    return False


def esperar_cair(segundos: float = 15.0) -> bool:
    """Espera a porta ficar livre — o servidor velho encerrou de fato."""
    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        if not no_ar():
            return True
        time.sleep(0.3)
    return False


def avisar(mensagem: str) -> None:
    """Aviso visível mesmo sob pythonw, onde stdout/stdin não existem."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, mensagem, "Second Brain", 0x10)
    except Exception:
        print(mensagem)


def reiniciar() -> int:
    """Troca de servidor sem janela, na mesma porta. Chamado como `--reiniciar`."""
    if not esperar_cair():
        avisar("O servidor antigo não encerrou a tempo.\n\nReabra o Second Brain.")
        return 1
    subir_servidor()
    if not esperar():
        avisar("O servidor não voltou a subir.\n\nVeja o erro em .servidor.log.")
        return 1
    return 0


def main() -> int:
    if "--reiniciar" in sys.argv:
        return reiniciar()

    if "--servir" in sys.argv:
        servir()
        return 0

    if no_ar():
        webbrowser.open(url())
        return 0

    escolher_porta()
    subir_servidor()
    if not esperar():
        avisar("O servidor não subiu a tempo.\n\n"
               "Veja o erro em .servidor.log, ou rode no terminal:\n"
               "    python -m uvicorn app.main:app")
        return 1

    webbrowser.open(url())
    return 0


if __name__ == "__main__":
    sys.exit(main())
