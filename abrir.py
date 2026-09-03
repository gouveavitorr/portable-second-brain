"""Sobe o servidor (se já não estiver no ar) e abre a tela "Agora" no navegador.

Pensado para ser chamado pelo atalho `iniciar.bat`, com um clique.

Se o app já estiver rodando, não sobe um segundo: só abre a aba.

Modo `--reiniciar`: usado pelo endpoint /api/reiniciar. Espera o servidor velho
cair, sobe um novo (escondido) e sai — sem abrir aba, porque a aba do usuário se
recarrega sozinha.
"""
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

PORTA = 8000
RAIZ = Path(__file__).resolve().parent
URL = f"http://127.0.0.1:{PORTA}"
LOG = RAIZ / ".servidor.log"


def no_ar() -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", PORTA)) == 0


def python_de_console() -> str:
    """O interpretador com console, mesmo se este script rodar sob pythonw.

    pythonw deixa sys.stdout = None; o uvicorn morre (rc=1) ao tentar logar.
    O servidor precisa de um python.exe de verdade.
    """
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe":
        console = exe.with_name("python.exe")
        if console.exists():
            return str(console)
    return str(exe)


def subir_servidor() -> None:
    # Sem janela de console: CREATE_NO_WINDOW esconde a janela e o log do uvicorn
    # vai para .servidor.log. Mantemos python.exe (não pythonw): a janela some, mas
    # o processo ainda é de console e o stdout aponta para um arquivo real — é o que
    # o uvicorn precisa para não morrer ao logar. .servidor.log é o indicador de
    # "por que não subiu" que a janela dava antes.
    sem_janela = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    log = open(LOG, "a", buffering=1, encoding="utf-8")
    subprocess.Popen(
        [python_de_console(), "-m", "uvicorn", "app.main:app", "--port", str(PORTA)],
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
    """Espera a porta ficar livre — o servidor velho encerrou de fato.

    Simétrico ao `esperar()`: no reinício, o novo não pode subir enquanto o velho
    ainda segura a porta.
    """
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
    """Troca de servidor sem janela. Chamado como `abrir.py --reiniciar`."""
    if not esperar_cair():
        avisar("O servidor antigo não encerrou a tempo.\n\n"
               "Reabra pelo iniciar.bat.")
        return 1
    subir_servidor()
    if not esperar():
        avisar("O servidor não voltou a subir.\n\n"
               "Veja o erro em .servidor.log.")
        return 1
    return 0


def main() -> int:
    if "--reiniciar" in sys.argv:
        return reiniciar()

    if no_ar():
        webbrowser.open(URL)
        return 0

    subir_servidor()
    if not esperar():
        avisar("O servidor não subiu a tempo.\n\n"
               "Veja o erro em .servidor.log, ou rode no terminal:\n"
               "    python -m uvicorn app.main:app")
        return 1

    webbrowser.open(URL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
