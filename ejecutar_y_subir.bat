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

where git.exe >nul 2>nul

if errorlevel 1 (
    for /d %%D in ("%LocalAppData%\GitHubDesktop\app-*") do (
        if exist "%%~fD\resources\app\git\cmd\git.exe" (
            set "GIT_EXE=%%~fD\resources\app\git\cmd\git.exe"
        )
    )
)

"%GIT_EXE%" --version
if errorlevel 1 (
    echo ERROR: No se encuentra Git.
    exit /b 1
)

"%GIT_EXE%" config user.name "Auto Bot"
"%GIT_EXE%" config user.email "bot@local.invalid"

echo.
echo [1/5] Descargando cambios de GitHub...

"%GIT_EXE%" -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=30 pull --ff-only

if errorlevel 1 (
    echo.
    echo ERROR: No se han podido descargar los cambios.
    echo No se ha forzado ningun rebase ni fusion.
    exit /b 1
)

echo.
echo [2/5] Actualizando listas...

"%PYTHON%" actualizar_elcano.py

if errorlevel 1 (
    echo ERROR en actualizar_elcano.py
    exit /b 1
)

echo.
echo [3/5] Eliminando lineas vacias...

"%PYTHON%" quitar_lineas_vacias.py

if errorlevel 1 (
    echo ERROR en quitar_lineas_vacias.py
    exit /b 1
)

echo.
echo [4/5] Preparando cambios...

"%GIT_EXE%" add -A

if errorlevel 1 (
    echo ERROR al preparar los archivos.
    exit /b 1
)

"%GIT_EXE%" diff --cached --quiet

if errorlevel 1 (
    "%GIT_EXE%" commit -m "Actualizacion automatica de listas"

    if errorlevel 1 (
        echo ERROR al crear el commit.
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
    exit /b 1
)

echo.
echo =====================================
echo       ACTUALIZACION COMPLETADA
echo =====================================
echo.

exit /b 0





