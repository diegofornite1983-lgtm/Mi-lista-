@echo off
cd /d "%~dp0"

set "GIT_EXE=git.exe"
where git.exe >nul 2>nul
if errorlevel 1 (
    for /d %%D in ("%LocalAppData%\GitHubDesktop\app-*") do (
        if exist "%%~fD\resources\app\git\cmd\git.exe" (
            set "GIT_EXE=%%~fD\resources\app\git\cmd\git.exe"
        )
    )
)

"%GIT_EXE%" config user.name >nul 2>nul || "%GIT_EXE%" config user.name "Auto Bot"
"%GIT_EXE%" config user.email >nul 2>nul || "%GIT_EXE%" config user.email "bot@local.invalid"

"%GIT_EXE%" rebase --abort >nul 2>nul
"%GIT_EXE%" merge --abort >nul 2>nul

"%GIT_EXE%" pull --rebase
if errorlevel 1 (
    echo Conflicto al traer cambios de la web. Abortando rebase...
    "%GIT_EXE%" rebase --abort >nul 2>nul
    exit /b 1
)

"C:\Users\diego\AppData\Local\Programs\Python\Python314\python.exe" actualizar_elcano.py
if errorlevel 1 (
    echo Error al actualizar las listas.
    exit /b 1
)

if exist "limpiar_hora.py" (
    "C:\Users\diego\AppData\Local\Programs\Python\Python314\python.exe" limpiar_hora.py
    if errorlevel 1 (
        echo Error en limpiar_hora.py.
        exit /b 1
    )
)

"%GIT_EXE%" add -A
"%GIT_EXE%" diff --cached --quiet
if errorlevel 1 (
    "%GIT_EXE%" commit -m "Subida automatica"
)

"%GIT_EXE%" push
if errorlevel 1 (
    echo Reintentando sincronizacion y push...
    "%GIT_EXE%" pull --rebase
    if errorlevel 1 (
        echo Conflicto en el segundo pull --rebase. Abortando rebase...
        "%GIT_EXE%" rebase --abort >nul 2>nul
        exit /b 1
    )
    "%GIT_EXE%" push
    if errorlevel 1 (
        echo Error en git push.
        exit /b 1
    )
)

exit /b 0



