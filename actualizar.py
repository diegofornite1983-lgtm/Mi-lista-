import urllib.request
import re
from pathlib import Path

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
                print("¡Descarga conseguida con éxito!")
                break
    except Exception as e:
        print(f"Fallo: {e}")

archivo_casa = Path("Mi lista acestream")
archivo_tailscale = Path("Canales m3u")

if not archivo_casa.exists():
    exit(0)

orig = archivo_casa.read_text(encoding="utf-8-sig", errors="replace")
if not fuente or "#EXTINF" not in fuente:
    exit(0)

fuente = fuente.replace("\r\n", "\n")
orig_norm = orig.replace("\r\n", "\n")

def normalizar(nombre):
    n = nombre.upper()
    n = re.sub(r'[\*\⭐️*]', '', n)
    n = re.sub(r'\b(720P|1080P|4K|HD|SD|FHD)\b', '', n)
    n = re.sub(r'M\+\s?|MOVISTAR\+\s?|MOVISTAR\s?PLUS\s?', 'MOVISTAR', n)
    return "".join(n.split())

# 1. Mapear los hashes nuevos de Elcano por nombre base normalizado
remotos_por_base = {}
lineas_f = fuente.split("\n")
i = 0
while i < len(lineas_f):
    linea = lineas_f[i].strip()
    if linea.startswith("#EXTINF:"):
        nombre_raw = linea.rsplit(",", 1)[-1].strip()
        base = normalizar(nombre_raw)
        j = i + 1
        while j < len(lineas_f):
            candidata = lineas_f[j].strip()
            if candidata and not candidata.startswith("#"):
                match_hash = re.search(r'([0-9a-fA-F]{40})', candidata)
                if match_hash:
                    h_val = match_hash.group(1)
                    if base not in remotos_por_base:
                        remotos_por_base[base] = []
                    remotos_por_base[base].append(h_val)
                break
            j += 1
    i += 1

print(f"Bases remotas encontradas: {len(remotos_por_base)}")

# 2. Recorrer la lista local respetando estrictamente el orden, nombres y estructura de Diego
lines = orig_norm.split("\n")
new_lines = []
i = 0
actualizados = 0

while i < len(lines):
    line = lines[i]
    new_lines.append(line)
    
    if line.startswith("#EXTINF:"):
        nombre_local = line.rsplit(",", 1)[-1].strip()
        base_local = normalizar(nombre_local)
        
        if i + 1 < len(lines) and not lines[i+1].startswith("#"):
            enlace_viejo = lines[i+1].strip()
            
            if base_local in remotos_por_base and remotos_por_base[base_local]:
                nuevo_hash = remotos_por_base[base_local][0]
                nuevo_enlace = re.sub(r'([0-9a-fA-F]{40})', nuevo_hash, enlace_viejo)
                new_lines.append(nuevo_enlace)
                actualizados += 1
            else:
                new_lines.append(enlace_viejo)
            i += 1
    i += 1

print(f"¡Sincronización quirúrgica completada! Canales con hash actualizado: {actualizados}")

lista_final_casa = "\n".join(new_lines) + "\n"
archivo_casa.write_text(lista_final_casa, encoding="utf-8")

# Generar automáticamente el archivo para Tailscale
lista_final_ts = lista_final_casa.replace("127.0.0.1:6878", "100.90.204.66:6878")
archivo_tailscale.write_text(lista_final_ts, encoding="utf-8")
