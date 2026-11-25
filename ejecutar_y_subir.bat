@echo off
cd /d "%~dp0"

"C:\Users\diego\AppData\Local\Programs\Python\Python314\python.exe" actualizar_elcano.py
if errorlevel 1 (
    echo Error al actualizar las listas.
    exit /b 1
)

"C:\Users\diego\AppData\Local\Programs\Python\Python314\python.exe" -c "import datetime, pathlib, re; stamp = f'# Ultima sincronizacion: {datetime.datetime.now().strftime(\"%%Y-%%m-%%d %%H:%%M:%%S\")}'; archivos = ['Canales m3u', 'Mi lista acestream', 'lista-amigos']; [p.write_text(re.sub(r'(?:\r?\n)?# Ultima sincronizacion:[^\r\n]*', '', re.sub(r'^(?:<<<<<<<|=======|>>>>>>>).*(\r?\n)?', '', p.read_text(encoding='utf-8', errors='replace'), flags=re.M)).rstrip('\r\n') + '\n' + stamp + '\n', encoding='utf-8') for nombre in archivos if (p := pathlib.Path(nombre)).exists()]"
if errorlevel 1 (
    echo Error al poner la marca de ultima sincronizacion.
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

"%GIT_EXE%" rebase --abort >nul 2>nul
"%GIT_EXE%" merge --abort >nul 2>nul

"%GIT_EXE%" add -A
"%GIT_EXE%" diff --cached --quiet
if errorlevel 1 (
    "%GIT_EXE%" commit -m "Subida automatica"
)

"%GIT_EXE%" pull --rebase
if errorlevel 1 (
    echo Conflicto en git pull --rebase. Abortando rebase para no dejarlo colgado...
    "%GIT_EXE%" rebase --abort >nul 2>nul
    exit /b 1
)

"%GIT_EXE%" push
if errorlevel 1 (
    echo Error en git push.
    exit /b 1
)

exit /b 0




