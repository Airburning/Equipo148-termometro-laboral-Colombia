@echo off
REM Se autolocaliza: no importa en que PC, con que usuario, o desde donde
REM lo ejecutes, siempre trabaja sobre la carpeta donde esta ESTE .bat.
cd /d "%~dp0"

echo ============================================================
echo   Instalando dependencias de Python para este proyecto...
echo ============================================================
echo.

if not exist "requirements.txt" (
    echo No se encontro requirements.txt en esta carpeta.
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
    echo.
    echo Instalalo desde https://www.python.org/downloads/
    echo IMPORTANTE: en el instalador marca la casilla "Add python.exe to PATH"
    echo antes de darle a Instalar. Luego vuelve a correr este archivo.
    echo.
    echo Si ya lo instalaste y sigues viendo este mensaje: cierra esta
    echo ventana, abre el menu Inicio, escribe cmd, abre una consola nueva,
    echo y prueba escribiendo  python --version  y  py --version  para ver
    echo cual de los dos funciona en este PC.
    echo.
    pause
    exit /b 1
)

echo Usando: %PYEXE%
%PYEXE% -m pip install --upgrade pip
%PYEXE% -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Algo fallo instalando las dependencias, revisa el mensaje de arriba.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Listo. Ahora puedes abrir "2_Abrir_App.bat".
echo ============================================================
pause
