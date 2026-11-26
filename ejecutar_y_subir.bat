@echo off
cd /d "%~dp0"
setlocal

set "PYTHON=C:\Users\diego\AppData\Local\Programs\Python\Python314\python.exe"
set "GIT_EXE=git.exe"
set "GIT_TERMINAL_PROMPT=0"

echo.
echo =====================================
echo       ACTUALIZADOR AUTOMATICO
echo =====================================
echo.

if not exist "%PYTHON%" (
    for /f "delims=" %%P in ('where python 2^>nul') do (
        set "PYTHON=%%P"
        goto :python_listo
    )
)
:python_listo

"%PYTHON%" --version >nul 2>nul
if errorlevel 1 (
    echo ERROR: No se encuentra Python.
    pause
    exit /b 1
)

where git.exe >nul 2>nul
if errorlevel 1 (
    for /d %%D in ("%LocalAppData%\GitHubDesktop\app-*") do (
        if exist "%%~fD\resources\app\git\cmd\git.exe" (
            set "GIT_EXE=%%~fD\resources\app\git\cmd\git.exe"
        )
    )
)

"%GIT_EXE%" --version >nul 2>nul
if errorlevel 1 (
    echo ERROR: No se encuentra Git.
    pause
    exit /b 1
)

"%GIT_EXE%" config user.name "Auto Bot"
"%GIT_EXE%" config user.email "bot@local.invalid"

echo.
echo [1/5] Descargando cambios de GitHub...

"%GIT_EXE%" -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=30 pull --ff-only
if errorlevel 1 (
    echo AVISO: pull --ff-only no pudo avanzar limpio. Continuando con la copia local...
)

echo.
echo [2/5] Actualizando listas...

if not exist "actualizar_elcano.py" (
    echo ERROR: No existe actualizar_elcano.py en %~dp0
    pause
    exit /b 1
)

"%PYTHON%" actualizar_elcano.py
if errorlevel 1 (
    echo.
    echo ERROR en actualizar_elcano.py
    pause
    exit /b 1
)

echo.
echo [3/5] Eliminando lineas vacias...

if not exist "quitar_lineas_vacias.py" (
    echo ERROR: No existe quitar_lineas_vacias.py en %~dp0
    pause
    exit /b 1
)

"%PYTHON%" quitar_lineas_vacias.py
if errorlevel 1 (
    echo.
    echo ERROR en quitar_lineas_vacias.py
    pause
    exit /b 1
)

echo.
echo [4/5] Preparando cambios...

"%GIT_EXE%" add -A
if errorlevel 1 (
    echo ERROR al preparar los archivos.
    pause
    exit /b 1
)

"%GIT_EXE%" diff --cached --quiet
if errorlevel 1 (
    "%GIT_EXE%" commit -m "Actualizacion automatica de listas"
    if errorlevel 1 (
        echo ERROR al crear el commit.
        pause
        exit /b 1
    )
) else (
    echo No hay cambios nuevos que guardar.
)

echo.
echo [5/5] Subiendo cambios a GitHub...

"%GIT_EXE%" -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=30 push
if errorlevel 1 (
    echo.
    echo ERROR al subir los cambios.
    echo Comprueba GitHub Desktop y vuelve a ejecutar.
    pause
    exit /b 1
)

echo.
echo =====================================
echo       ACTUALIZACION COMPLETADA
echo =====================================
echo.

pause
exit /b 0





