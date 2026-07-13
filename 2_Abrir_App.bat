@echo off
REM Se autolocaliza (ver nota en 1_Instalar.bat) - funciona sin importar en
REM que PC ni con que usuario estes, mientras el repositorio completo
REM viaje junto (con app\, src\, data\ y models\ adentro).
cd /d "%~dp0"

if not exist "app\dashboard_app.py" (
    echo No se encontro app\dashboard_app.py en esta carpeta.
    echo.
    echo Parece que solo copiaste este archivo .bat, sin el resto del
    echo repositorio. Clona o copia el repositorio COMPLETO a este PC.
    echo.
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

if not exist "data\04_model_output\report_data.json" (
    echo No se encontraron los datos del modelo todavia.
    echo Corre primero "1_Instalar.bat" y luego "3_Actualizar_Datos.bat".
    pause
    exit /b 1
)

%PYEXE% app\dashboard_app.py

if errorlevel 1 (
    echo.
    echo La app se cerro con un error, revisa el mensaje de arriba.
    echo Si dice algo de "No module named ...", corre "1_Instalar.bat" primero.
    pause
)
