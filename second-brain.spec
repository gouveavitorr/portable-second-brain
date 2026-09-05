# -*- mode: python ; coding: utf-8 -*-
"""Empacotamento do Second Brain num único .exe (PyInstaller).

Não rode direto: use o `build.bat`, que limpa o lixo de runtime do vault semente
antes (senão o .cache da PokeAPI e o progresso.json entram no pacote à toa).

    build.bat        # ou: pyinstaller second-brain.spec

Gera `dist/Second Brain.exe` — um arquivo só, que a pessoa baixa e clica. Sem Python
instalado, sem pip, offline. O entry-point é o `abrir.py` (o launcher).
"""
import os
from PyInstaller.utils.hooks import collect_submodules

# Ícone opcional: se você largar um `build/icone.ico` no repo, o exe usa ele; senão,
# o PyInstaller usa o ícone padrão dele (não dá erro).
_icone = "build/icone.ico" if os.path.exists("build/icone.ico") else None

# uvicorn importa loop/protocolo dinamicamente ("auto"); sem isto, o exe sobe mas
# o servidor não acha o backend de asyncio/http.
hiddenimports = collect_submodules("uvicorn")

# Recursos versionados que vão pra dentro do exe (extraídos em sys._MEIPASS em runtime):
# - static/ : telas + sprites (static/pokemon/*.png) + cadeias.json + fontes
# - second_brain/ : a semente do vault, copiada pra Documentos/SecondBrain na 1a execução
#   (o build.bat já removeu .cache/ e progresso.json; preparar_vault ignora de novo)
datas = [
    ("static", "static"),
    ("second_brain", "second_brain"),
]

# Nada disto é usado em runtime (o app é offline e não fala com LLM nenhum). Excluir
# encolhe o exe e evita o PyInstaller puxar dependência pesada à toa.
excludes = [
    "anthropic",
    "google", "google_auth_oauthlib", "googleapiclient",
    "pytest", "_pytest",
    "tkinter",
]

a = Analysis(
    ["abrir.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Second Brain",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # windowed: nada de janela de console ao clicar
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_icone,            # ver o topo do arquivo
)
