@echo off
cd /d "%~dp0"

"C:\Users\diego\AppData\Local\Programs\Python\Python314\python.exe" actualizar_elcano.py
if errorlevel 1 (
    echo Error al actualizar las listas.
    pause
    exit /b 1
)

echo Listas actualizadas. Ahora abre GitHub Desktop para subir los cambios.
pause

