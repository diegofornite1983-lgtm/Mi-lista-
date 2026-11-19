@echo off
cd /d "%~dp0"

"C:\Users\diego\AppData\Local\Programs\Python\Python314\python.exe" actualizar_elcano.py
if errorlevel 1 (
    echo Error al actualizar las listas.
    pause
    exit /b 1
)

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

"%GIT_EXE%" pull --rebase --autostash
if errorlevel 1 (
    echo Error en git pull.
    pause
    exit /b 1
)

"%GIT_EXE%" add -A
"%GIT_EXE%" commit -m "Subida automatica"
"%GIT_EXE%" push
if errorlevel 1 (
    echo Error en git push.
    pause
    exit /b 1
)

echo Todo actualizado y subido.
exit /b 0