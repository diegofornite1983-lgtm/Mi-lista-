import pathlib
import re

archivos = ["Canales m3u", "Mi lista acestream", "lista-amigos"]

for nombre in archivos:
    ruta = pathlib.Path(nombre)
    if ruta.exists():
        lineas = ruta.read_text(encoding="utf-8", errors="replace").splitlines()
        limpias = []
        for linea in lineas:
            limpia = linea.strip()
            if not limpia:
                continue
            if limpia.startswith(("<<<<<<<", "=======", ">>>>>>>")):
                continue
            if limpia.startswith("# Ultima sincronizacion:"):
                continue
            limpias.append(limpia)
        ruta.write_text("\n".join(limpias) + "\n", encoding="utf-8")


