import pathlib
import re

archivos = ["Canales m3u", "Mi lista acestream", "lista-amigos"]

for nombre in archivos:
    ruta = pathlib.Path(nombre)
    if ruta.exists():
        texto = ruta.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        texto = re.sub(r"^(?:<<<<<<<|=======|>>>>>>>).*(\n)?", "", texto, flags=re.M)
        texto = re.sub(r"(?:\n)?# Ultima sincronizacion:[^\n]*", "", texto)
        texto = re.sub(r"\n{2,}", "\n", texto).strip()
        ruta.write_text(texto + "\n", encoding="utf-8")

