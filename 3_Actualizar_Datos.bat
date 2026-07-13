@echo off
REM Se autolocaliza. Vuelve a leer las 6 fuentes de data\01_raw\ y
REM regenera todo: paneles intermedios, modelo, proyeccion, dashboard web
REM y los datos que usa la app de escritorio.
cd /d "%~dp0"

if not exist "pipelines\pipeline_ml.py" (
    echo No se encontro pipelines\pipeline_ml.py en esta carpeta.
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

%PYEXE% pipelines\pipeline_ml.py

if errorlevel 1 (
    echo.
    echo Algo fallo regenerando los datos, revisa el mensaje de arriba.
    echo Si dice algo de "No module named ...", corre "1_Instalar.bat" primero.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Listo. Abre "2_Abrir_App.bat" o reports\reporte_final.html para verlo.
echo ============================================================
pause
