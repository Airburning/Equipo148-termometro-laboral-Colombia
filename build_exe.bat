@echo off
REM Empaqueta app\dashboard_app.py como un .exe independiente (no necesita
REM Python instalado para ejecutarse despues). Correr este script EN
REM WINDOWS - doble clic funciona desde cualquier PC/usuario, se
REM autolocaliza.
REM
REM NOTA: al mover el proyecto a la estructura de repo (app/, src/, data/,
REM models/, reports/) el .exe generado necesita esas carpetas junto a el
REM para encontrar report_data.json y los CSV de la pestana "6. Datos" -
REM revisa los --add-data de abajo si cambias esa estructura.
REM
REM Uso:
REM   1. Doble clic en 1_Instalar.bat (una vez)
REM   2. Doble clic en build_exe.bat
REM   3. El ejecutable queda en dist\PanelDesempleoRegional.exe
cd /d "%~dp0"

if not exist "app\dashboard_app.py" (
    echo No se encontro app\dashboard_app.py en esta carpeta.
    echo Clona o copia el repositorio COMPLETO a este PC.
    pause
    exit /b 1
)

set "PYEXE="
where python >nul 2>nul
if not errorlevel 1 set "PYEXE=python"

if not defined PYEXE (
    where py >nul 2>nul
    if not errorlevel 1 set "PYEXE=py"
)

if not defined PYEXE (
    echo No se encontro Python instalado en este PC.
    echo Corre primero "1_Instalar.bat" - ahi te explica como instalarlo.
    pause
    exit /b 1
)

%PYEXE% -m pip install pyinstaller
%PYEXE% -m PyInstaller --noconfirm --onefile --windowed ^
  --name "PanelDesempleoRegional" ^
  --add-data "src;src" ^
  --add-data "data\04_model_output;data\04_model_output" ^
  --add-data "data\03_primary;data\03_primary" ^
  --add-data "data\02_intermediate;data\02_intermediate" ^
  --paths "src" ^
  app\dashboard_app.py

echo.
echo Listo. Ejecutable en dist\PanelDesempleoRegional.exe
echo Copialo junto con la carpeta "data" si quieres moverlo a otra PC,
echo o vuelve a generarlo ahi con este mismo script.
pause
