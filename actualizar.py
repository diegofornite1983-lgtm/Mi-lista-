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

path = Path("Mi lista acestream")
if not path.exists():
    exit(0)

orig = path.read_text(encoding="utf-8-sig", errors="replace")
if not fuente or "#EXTINF" not in fuente:
    exit(0)

fuente = fuente.replace("\r\n", "\n")
orig_norm = orig.replace("\r\n", "\n")

def extraer_base(nombre):
    n = nombre.upper()
    n = re.sub(r'\b(720P|1080P|4K|HD|SD|FHD)\b', '', n)
    n = re.sub(r'[\*⭐️*]', '', n)
    n = re.sub(r'M\+\s?|MOVISTAR\+\s?|MOVISTAR\s?PLUS\s?', 'MOVISTAR', n)
    n = re.sub(r'\s+[0-9]+$', '', n)
    return "".join(n.split())

hashes_por_base = {}
lineas_f = fuente.split("\n")
i = 0
while i < len(lineas_f):
    linea = lineas_f[i].strip()
    if linea.startswith("#EXTINF:"):
        nombre_raw = linea.rsplit(",", 1)[-1].strip()
        base = extraer_base(nombre_raw)
        
        j = i + 1
        while j < len(lineas_f):
            candidata = lineas_f[j].strip()
            if candidata and not candidata.startswith("#"):
                match_hash = re.search(r'([0-9a-fA-F]{40})', candidata)
                if match_hash:
                    link_ace = f"http://127.0.0.1:6878/ace/getstream?id={match_hash.group(1)}"
                    if base not in hashes_por_base:
                        hashes_por_base[base] = []
                    hashes_por_base[base].append(link_ace)
                break
            j += 1
    i += 1

print(f"Bases de canales encontradas en la fuente remota: {len(hashes_por_base)}")

lines = orig_norm.split("\n")
new_lines = []
i = 0
actualizados = 0
indices_uso = {}

while i < len(lines):
    line = lines[i]
    new_lines.append(line)
    if line.startswith("#EXTINF:"):
        nombre_canal = line.rsplit(",", 1)[-1].strip()
        base = extraer_base(nombre_canal)
        
        if i + 1 < len(lines) and not lines[i+1].startswith("#"):
            lista_candidatos = []
            if base in hashes_por_base:
                lista_candidatos = hashes_por_base[base]
            else:
                for b_key, b_vals in hashes_por_base.items():
                    if b_key in base or base in b_key:
                        lista_candidatos = b_vals
                        break

            if lista_candidatos:
                idx = indices_uso.get(base, 0)
                link_asignado = lista_candidatos[idx % len(lista_candidatos)]
                indices_uso[base] = idx + 1
                
                new_lines.append(link_asignado)
                actualizados += 1
            else:
                new_lines.append(lines[i+1])
            i += 1
    i += 1

print(f"¡Canales sincronizados y actualizados con éxito: {actualizados}!")
path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
