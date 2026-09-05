@echo off
rem Empacota o Second Brain num unico .exe (dist\Second Brain.exe).
rem Roda na SUA maquina, com internet na primeira vez (pra baixar o PyInstaller).
rem NAO vai pro usuario final: o que ele recebe eh so o .exe de dist\.
cd /d "%~dp0"

echo == 1/4 limpando lixo de runtime do vault semente ==
rem (senao o cache da PokeAPI e o progresso do dev entram no pacote a toa)
if exist "second_brain\.cache" rmdir /s /q "second_brain\.cache"
if exist "second_brain\progresso.json" del /q "second_brain\progresso.json"
if exist "second_brain\estado.md" del /q "second_brain\estado.md"
if exist "second_brain\.primeira-vez" del /q "second_brain\.primeira-vez"

echo == 2/4 conferindo que os sprites foram baixados ==
if not exist "static\pokemon\cadeias.json" (
  echo.
  echo FALTA rodar o build de sprites primeiro, senao o app nao roda offline:
  echo     python -m scripts.baixar_sprites
  exit /b 1
)

echo == 3/4 instalando dependencias de build ==
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :erro

echo == 4/4 empacotando (isto demora um pouco) ==
python -m PyInstaller --noconfirm --clean second-brain.spec
if errorlevel 1 goto :erro

echo.
echo Pronto. O executavel esta em:  dist\Second Brain.exe
echo Teste ele num perfil/pasta SEM Python no PATH antes de distribuir.
goto :fim

:erro
echo.
echo FALHOU. Veja o erro acima.
exit /b 1

:fim
