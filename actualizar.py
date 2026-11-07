import urllib.request
from pathlib import Path

# URLs de la lista de Elcano
urls = [
    "https://tokyo2.elcano-ipfs.workers.dev/k51qzi5uqu5dh5qej4b9wlcr5i6vhc7rcfkekhrxqek5c9lk6gdaiik820fecs/hashes_acestream.m3u",
    "https://ipfs.io/ipns/k51qzi5uqu5dh5qej4b9wlcr5i6vhc7rcfkekhrxqek5c9lk6gdaiik820fecs/hashes_acestream.m3u"
]

fuente = None
for url in urls:
    try:
        print(f"Probando pasarela: {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as res:
            fuente = res.read().decode("utf-8-sig", errors="replace")
            if fuente and "#EXTINF" in fuente:
                print("¡Descarga de Elcano conseguida con éxito!")
                break
    except Exception as e:
        print(f"Fallo: {e}")

if not fuente or "#EXTINF" not in fuente:
    exit("ERROR: No se pudo descargar la lista de Elcano.")

# Normalizar saltos de línea
fuente = fuente.replace("\r\n", "\n")

# Archivos de salida en tu repositorio
archivo_casa = Path("Mi lista acestream")
archivo_tailscale = Path("Canales m3u")

# Guardar la lista limpia directamente en tu archivo base
archivo_casa.write_text(fuente, encoding="utf-8")
print("¡Lista de Elcano volcada en 'Mi lista acestream' correctamente!")

# Generar automáticamente la versión para Tailscale cambiando la IP local del motor AceStream
lista_tailscale = fuente.replace("127.0.0.1:6878", "100.90.204.66:6878")
archivo_tailscale.write_text(lista_tailscale, encoding="utf-8")
print("¡Versión de Tailscale generada correctamente!")
