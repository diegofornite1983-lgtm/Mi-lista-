import datetime
import pathlib
import re

ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
marca = f"# Ultima sincronizacion: {ahora}"
archivos = ["Canales m3u", "Mi lista acestream", "lista-amigos"]

for nombre in archivos:
    ruta = pathlib.Path(nombre)
    if ruta.exists():
        texto = ruta.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        texto = re.sub(r"^(?:<<<<<<<|=======|>>>>>>>).*(\n)?", "", texto, flags=re.M)
        texto = re.sub(r"(?:\n)?# Ultima sincronizacion:[^\n]*", "", texto)
        texto = re.sub(r"\n{2,}", "\n", texto).strip("\n")
        ruta.write_text(texto + "\n" + marca + "\n", encoding="utf-8")
