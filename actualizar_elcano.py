import datetime
import gzip
import io
import json
import re
import sys
import time
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

# ==========================================================
# CONFIGURACION
# ==========================================================

CARPETA_LISTAS = Path(__file__).resolve().parent

IPNS_HASH = "k51qzi5uqu5dh5qej4b9wlcr5i6vhc7rcfkekhrxqek5c9lk6gdaiik820fecs"

URLS_ELCANO = [
    f"http://127.0.0.1:8080/ipns/{IPNS_HASH}/hashes_acestream.m3u",
    f"http://127.0.0.1:8080/ipns/{IPNS_HASH}/hashes.json",
    f"https://ipfs.bytokyo.dpdns.org/{IPNS_HASH}/hashes_acestream.m3u",
    f"https://ipfs2.bytokyo.dpdns.org/{IPNS_HASH}/hashes_acestream.m3u",
    f"https://tokyo2.elcano-ipfs.workers.dev/{IPNS_HASH}/hashes_acestream.m3u",
    f"https://ipfs.io/ipns/{IPNS_HASH}/hashes_acestream.m3u",
    f"https://gateway.pinata.cloud/ipns/{IPNS_HASH}/hashes_acestream.m3u",
    f"https://cloudflare-ipfs.com/ipns/{IPNS_HASH}/hashes_acestream.m3u",
    f"https://dweb.link/ipns/{IPNS_HASH}/hashes_acestream.m3u",
    f"https://w3s.link/ipns/{IPNS_HASH}/hashes_acestream.m3u",
]

archivo_casa = CARPETA_LISTAS / "Mi lista acestream"
archivo_tailscale = CARPETA_LISTAS / "Canales m3u"
archivo_amigos = CARPETA_LISTAS / "lista-amigos"

# LOGOTIPO LIMPIO SIN ESPACIOS NI PARENTESIS (MOVISTAR PLUS Y M+ 0)
URL_LOGO_PERSONAL = "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/Movistar%20Plus.png"

TGV_ID_MOVISTAR_UNIFICADO = "Movistar Plus HD"

GROUP_TITLE = "⭐ ELCANO [MÁXIMA CALIDAD]"

URLS_EPG = [
    "https://raw.githubusercontent.com/davidmuma/EPG_dobleM/refs/heads/master/guiatv.xml",
    "https://epgshare01.online/epgshare01/epg_ripper_US_SPORTS1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_US1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_NL1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_PT1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_TR1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_IT1.xml.gz",
]
CACHE_EPG = CARPETA_LISTAS / "cache_ids_epg.json"

DOMINIOS_SUCIOS = (
    "adslzone.net",
    "movistarplus.es/recorte",
    "fandom.com",
    "wikia.nocookie.net",
    "pbs.twimg.com/profile_images",
    "yt3.googleusercontent.com",
    "hearstapps",
    "vhv.rs",
    "pngegg",
    "bluestacks",
    "arcpublishing",
    "sincroguia",
    "sportsvideo",
)

# ==========================================================
# COMPROBAR ARCHIVO PRINCIPAL
# ==========================================================

if not archivo_casa.is_file():
    sys.exit(
        f"ERROR: No se encuentra el archivo '{archivo_casa}'. "
        "No se modifica ningun archivo."
    )

try:
    contenido_casa = archivo_casa.read_bytes().decode("utf-8-sig")
except UnicodeDecodeError:
    try:
        contenido_casa = archivo_casa.read_bytes().decode("latin-1")
    except Exception as error:
        sys.exit(f"ERROR leyendo la lista principal: {error}")

salto = "\r\n" if "\r\n" in contenido_casa else "\n"

# ==========================================================
# LOCALIZAR Y PROTEGER LAS CARPETAS PERSONALES
# ==========================================================

lineas_casa = contenido_casa.splitlines(keepends=True)

marcador_personal = re.compile(
    r"^\s*#?\s*(CARPETA:|ZONA PERSONAL:|SECCI[ÓO]N:)",
    re.IGNORECASE,
)

indice_personal = None

for indice, linea in enumerate(lineas_casa):
    if marcador_personal.search(linea):
        indice_personal = indice
        break

if indice_personal is None:
    sys.exit(
        "ERROR DE SEGURIDAD: No se ha encontrado el comienzo "
        "de tus carpetas personales (CARPETA:, ZONA PERSONAL: "
        "o SECCION:). No se modifica ni sobrescribe ningun archivo."
    )

inicio_personal = indice_personal

while inicio_personal > 0:
    anterior = lineas_casa[inicio_personal - 1].strip()

    if not anterior or re.fullmatch(r"#\s*=+", anterior):
        inicio_personal -= 1
    else:
        break

cuerpo_personal = "".join(lineas_casa[inicio_personal:])

# ==========================================================
# DESCARGAR ELCANO (PROBANDO VARIAS URLS)
# ==========================================================

fuente_elcano = None
errores_descarga = []

for url_intento in URLS_ELCANO:
    try:
        peticion = urllib.request.Request(
            url_intento,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "*/*",
            },
        )

        with urllib.request.urlopen(peticion, timeout=30) as respuesta:
            texto_leido = respuesta.read().decode("utf-8-sig", errors="replace")
            if "#EXTINF:" in texto_leido or "acestream://" in texto_leido:
                fuente_elcano = texto_leido
                print(f"Fuente cargada desde: {url_intento}")
                break
            else:
                errores_descarga.append(
                    f"{url_intento} -> Respuesta sin formato M3U (#EXTINF:)"
                )
    except Exception as error:
        errores_descarga.append(f"{url_intento} -> {error}")

if not fuente_elcano:
    sys.exit(
        "ERROR descargando Elcano desde todas las URLs disponibles:\n"
        + "\n".join(errores_descarga)
        + "\nNo se modifica ningun archivo."
    )

# ==========================================================
# FUNCIONES AUXILIARES Y REFERENCIA DE CARPETAS PERSONALES
# ==========================================================


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caracter for caracter in texto if unicodedata.category(caracter) != "Mn"
    )
    return texto.upper().strip()


def clave_canal(texto):
    n = normalizar(texto)
    n = re.sub(r"[⭐⭐️*]", "", n)
    n = re.sub(
        r"\b(1080P|720P|4K|FHD|HD|SD|SHICKAT|ELCANO|CANO|SOLO EVENTOS)\b",
        "",
        n,
    )
    n = re.sub(r"\[.*?\]|\(.*?\)", "", n)
    n = re.sub(r"\s+[0-9A-F]{3,5}\b", "", n)
    n = re.sub(r"#\d+", "", n)
    n = n.replace("MOVISTAR+", "M+")
    n = n.replace("LA LIGA", "LALIGA").replace("FORMULA 1", "F1")
    n = re.sub(r"\s+", " ", n).strip()
    return n


def extraer_mapa_personal(texto_personal):
    mapa = {}
    for linea in texto_personal.splitlines():
        if not linea.startswith("#EXTINF:") or "," not in linea:
            continue
        m_id = re.search(r'tvg-id="([^"]+)"', linea, flags=re.IGNORECASE)
        if not m_id:
            continue
        nombre_c = linea.rsplit(",", 1)[-1].strip()
        k = clave_canal(nombre_c)
        if k and k not in mapa:
            mapa[k] = m_id.group(1)
    return mapa


def cargar_ids_epg():
    """Lee IDs reales de XMLTV para completar tvg-id antes de escribir la M3U."""
    ahora = time.time()
    try:
        cache = json.loads(CACHE_EPG.read_text(encoding="utf-8"))
        if ahora - float(cache.get("timestamp", 0)) < 6 * 3600:
            return set(cache.get("ids", [])), dict(cache.get("nombres", {}))
    except Exception:
        pass

    ids = set()
    nombres = {}
    for url in URLS_EPG:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/xml,text/xml,*/*",
                },
            )
            with urllib.request.urlopen(req, timeout=35) as respuesta:
                datos = respuesta.read()
            if datos[:2] == b"\x1f\x8b":
                datos = gzip.decompress(datos)
            for _, elemento in ET.iterparse(io.BytesIO(datos), events=("end",)):
                if elemento.tag.rsplit("}", 1)[-1] == "channel":
                    canal_id = (elemento.attrib.get("id") or "").strip()
                    if canal_id:
                        ids.add(canal_id)
                        for display in list(elemento):
                            if display.tag.rsplit("}", 1)[-1] == "display-name":
                                nombre_epg = " ".join("".join(display.itertext()).split())
                                clave = clave_canal(nombre_epg)
                                if clave:
                                    nombres.setdefault(clave, canal_id)
                    elemento.clear()
        except Exception:
            pass

    if ids:
        try:
            CACHE_EPG.write_text(
                json.dumps(
                    {"timestamp": ahora, "ids": sorted(ids), "nombres": nombres},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass
    return ids, nombres


def buscar_id_epg(nombre):
    """Busca el ID XMLTV por nombre exacto y después por alias controlados."""
    clave = clave_canal(nombre)

    if clave in MAPA_EPG_NOMBRE:
        return MAPA_EPG_NOMBRE[clave]

    alias = {
        "ESPORT3": (
            "ESPORT 3",
            "TV3 ESPORTS",
            "ESPORT3 HD",
        ),
        "NBA LEAGUE PASS": (
            "NBA LEAGUE PASS",
            "NBA LEAGUE PASS 1",
            "NBA LEAGUE PASS 2",
            "NBA LEAGUE PASS 3",
            "NBA LEAGUE PASS HD",
            "NBA LEAGUE PASS 1080P",
        ),
        "NBA ESPN": (
            "ESPN NBA",
            "NBA ON ESPN",
            "ESPN",
        ),
        "UFC": (
            "UFC",
            "UFC HD",
            "UFC TV",
            "UFC TV HD",
            "UFC FIGHT PASS",
            "UFC FIGHT PASS HD",
            "UFC NETWORK",
            "UFC NETWORK HD",
        ),
          "BEIN SPORTS 3 TR": (
            "BEIN SPORTS 3",
            "BEIN SPORTS 3 HD",
            "BEIN SPORTS 3 TURKEY",
        ),
        "BEIN SPORTS TR": (
            "BEIN SPORTS HABER",
            "BEIN SPORTS TR HD",
            "BEIN SPORTS TURKEY",
        ),
        "BEIN SPORTS 2 TR": (
            "BEIN SPORTS 2",
            "BEIN SPORTS 2 HD",
            "BEIN SPORTS 2 TURKEY",
        ),
        "DAZN LALIGA 3": (
            "DAZN LALIGA 3 HD",
            "DAZN LALIGA 3",
        ),
    }

    for candidato in alias.get(clave, ()):
        id_real = MAPA_EPG_NOMBRE.get(clave_canal(candidato))
        if id_real:
            return id_real

    if clave == "BEIN SPORTS 3 TR":
        for id_candidato in (
            "beIN.SPORTS.3.tr",
            "Beinsports.3.tr",
        ):
            if id_candidato in IDS_EPG_DISPONIBLES:
                return id_candidato
    if clave == "BEIN SPORTS 2 TR":
        for id_candidato in (
            "beIN.SPORTS.2.tr",
            "Beinsports.2.tr",
            "bein-sports-2-tr",
        ):
            if id_candidato in IDS_EPG_DISPONIBLES:
                return id_candidato

    if clave == "NBA LEAGUE PASS":
        candidatos_nba = sorted(
            (
                (nombre_epg, id_epg)
                for nombre_epg, id_epg in MAPA_EPG_NOMBRE.items()
                if nombre_epg.startswith("NBA LEAGUE PASS ")
                and id_epg in IDS_EPG_DISPONIBLES
            ),
            key=lambda item: item[0],
        )
        if candidatos_nba:
            return candidatos_nba[0][1]

    if clave in ("NBA LEAGUE PASS", "UFC"):
        tokens = clave.split()
        candidatos = []
        for k, v in MAPA_EPG_NOMBRE.items():
            palabras = k.split()
            if len(palabras) >= len(tokens) and palabras[: len(tokens)] == tokens:
                candidatos.append((k, v))
        candidatos.sort(key=lambda item: (len(item[0]), item[0]))
        if candidatos:
            return candidatos[0][1]

    if clave not in ("UFC", "NBA ESPN"):
        prefijos = (clave + " ",)
        candidatos = sorted(
            (
                (k, v)
                for k, v in MAPA_EPG_NOMBRE.items()
                if any(k.startswith(prefijo) for prefijo in prefijos)
            ),
            key=lambda item: (len(item[0]), item[0]),
        )
        if candidatos:
            return candidatos[0][1]

    return None


def ajustar_id_con_epg(linea, nombre):
    """Asegura que tvg-id coincida con un channel id real de XMLTV."""
    if not IDS_EPG_DISPONIBLES:
        return linea

    actual = re.search(
        r'tvg-id="([^"]*)"',
        linea,
        flags=re.IGNORECASE,
    )

    clave = clave_canal(nombre)

    if clave in ("NBA LEAGUE PASS", "UFC", "BEIN SPORTS 3 TR", "BEIN SPORTS 2 TR"):
        id_real = buscar_id_epg(nombre)
        if id_real:
            linea = poner_atributo(linea, "tvg-id", id_real)
            return poner_atributo(linea, "tvg-name", nombre)

    if actual and actual.group(1) in IDS_EPG_DISPONIBLES:
        return poner_atributo(linea, "tvg-name", nombre)

    id_real = buscar_id_epg(nombre)

    if id_real:
        linea = poner_atributo(linea, "tvg-id", id_real)
        return poner_atributo(linea, "tvg-name", nombre)

    linea = quitar_atributo(linea, "tvg-id")
    return poner_atributo(linea, "tvg-name", nombre)


IDS_EPG_DISPONIBLES, MAPA_EPG_NOMBRE = cargar_ids_epg()
MAPA_PERSONAL_ID = extraer_mapa_personal(cuerpo_personal)


def poner_atributo(linea, atributo, valor):
    patron = rf'{re.escape(atributo)}="[^"]*"'

    if re.search(patron, linea, flags=re.IGNORECASE):
        return re.sub(
            patron,
            f'{atributo}="{valor}"',
            linea,
            count=1,
            flags=re.IGNORECASE,
        )

    return linea.replace("#EXTINF:-1", f'#EXTINF:-1 {atributo}="{valor}"', 1)


def quitar_atributo(linea, atributo):
    linea = re.sub(rf'\s*{re.escape(atributo)}="[^"]*"', "", linea, flags=re.IGNORECASE)
    linea = re.sub(r"\s+", " ", linea)
    return linea.replace("#EXTINF:-1 ", "#EXTINF:-1 ")


def limpiar_y_forzar_movistar(linea):
    linea = quitar_atributo(linea, "tvg-id")
    linea = quitar_atributo(linea, "tvg-logo")
    nuevo_sufijo = (
        f'tvg-id="{TGV_ID_MOVISTAR_UNIFICADO}" tvg-logo="{URL_LOGO_PERSONAL}"'
    )
    return linea.replace("#EXTINF:-1", f"#EXTINF:-1 {nuevo_sufijo}", 1)


def limpiar_logo_si_es_sucio(linea):
    coincidencia = re.search(r'tvg-logo="([^"]*)"', linea, flags=re.IGNORECASE)
    if not coincidencia:
        return linea
    logo_actual = coincidencia.group(1).lower()
    if any(sucio in logo_actual for sucio in DOMINIOS_SUCIOS):
        return quitar_atributo(linea, "tvg-logo")
    return linea


def numero_canal(nombre):
    coincidencia = re.search(r"\b([1-9])\b", nombre)
    if coincidencia:
        return int(coincidencia.group(1))
    return 0


def calidad_canal(nombre):
    if "4K" in nombre:
        return 0
    if "1080" in nombre:
        return 1
    if "720" in nombre:
        return 2
    return 3


# ==========================================================
# ORDEN ESTRICTO DE CANALES
# ==========================================================


def prioridad_canal(canal):
    nombre_original = canal["nombre"]
    nombre = normalizar(nombre_original)

    numero = numero_canal(nombre)
    calidad = calidad_canal(nombre)

    if nombre.startswith("MOVISTAR PLUS") or nombre.startswith("MOVISTAR+"):
        return (0, 0, calidad, canal["indice"])

    if re.search(r"\bM\+\s*0\b", nombre):
        return (1, 0, calidad, canal["indice"])

    if (
        "LALIGA" in nombre or "LA LIGA" in nombre or "DAZN LALIGA" in nombre
    ) and "HYPERMOTION" not in nombre:
        if nombre.startswith("M+"):
            suborden = 0
        elif "DAZN" in nombre:
            suborden = 1
        else:
            suborden = 2
        return (2, suborden, numero, calidad, canal["indice"])

    if "CAMPEONES" in nombre or "CHAMPIONS" in nombre:
        return (3, numero, calidad, canal["indice"])

    if "DEPORTES" in nombre and "BALONCESTO" not in nombre:
        return (4, numero, calidad, canal["indice"])

    if re.search(r"\bF1\b", nombre) or "FORMULA 1" in nombre:
        return (5, 0, calidad, canal["indice"])

    if "MOTOGP" in nombre:
        return (5, 1, calidad, canal["indice"])

    if "DAZN" in nombre and not any(
        palabra in nombre
        for palabra in ("F1", "FORMULA", "MOTOGP", "LALIGA", "BALONCESTO")
    ):
        return (6, numero, calidad, canal["indice"])

    if "VAMOS" in nombre:
        return (7, 0, numero, calidad, canal["indice"])

    if "HYPERMOTION" in nombre:
        return (8, 0, numero, calidad, canal["indice"])

    if "RFEF" in nombre or "PRIMERA FEDERACION" in nombre:
        return (9, 0, nombre, calidad, canal["indice"])

    if "GOLF" in nombre:
        return (10, 0, numero, calidad, canal["indice"])

    if "EUROSPORT" in nombre:
        return (10, 1, numero, calidad, canal["indice"])

    if "TENIS" in nombre or "TENNIS" in nombre:
        return (10, 2, numero, calidad, canal["indice"])

    if "SPORT TV" in nombre:
        return (10, 3, numero, calidad, canal["indice"])

    if (
        "BALONCESTO" not in nombre
        and not nombre.startswith("NBA")
        and not es_tdt_abierto(nombre)
    ):
        return (11, 0, nombre, calidad, canal["indice"])

    if "BALONCESTO" in nombre or nombre.startswith("NBA"):
        return (12, numero, calidad, canal["indice"])

    if es_tdt_abierto(nombre):
        return (13, 0, nombre, calidad, canal["indice"])

    return (11, 0, nombre, calidad, canal["indice"])


def es_tdt_abierto(nombre):
    canales_abiertos = (
        "CUATRO",
        "TELECINCO",
        "TELEDEPORTE",
        "ESPORT3",
        "A PUNT",
        "APUNT",
        "LA 1",
        "LA 2",
        "LA 3",
        "TVE",
        "ANTENA 3",
        "ANTENA3",
        "LA SEXTA",
        "LASEXTA",
        "REAL MADRID TV",
        "ONETORO",
        "ONE TORO",
    )
    return any(canal in nombre for canal in canales_abiertos)


PICONS_BASE = "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon"
TV_LOGOS_ES = "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/spain"
TV_LOGOS_US = "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-states"
TV_LOGOS_IT = "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/hd"
TV_LOGOS_TR = "https://raw.githubusercontent.com/tv-logo/tv-logos/refs/heads/main/countries/turkey"


def resolver_tvg_id(nombre_norm, nombre_original, id_por_defecto):
    clave = clave_canal(nombre_original or nombre_norm)
    if clave and clave in MAPA_PERSONAL_ID:
        return MAPA_PERSONAL_ID[clave]
    return id_por_defecto


def aplicar_logo_y_epg(linea, nombre_norm, nombre_original=""):
    linea = limpiar_logo_si_es_sucio(linea)

    if re.search(r"\bM\+\s*0\b", nombre_norm) or (
        nombre_norm.startswith("MOVISTAR PLUS") or nombre_norm.startswith("MOVISTAR+")
    ):
        return limpiar_y_forzar_movistar(linea)

    if "CAMPEONES" in nombre_norm or "CHAMPIONS" in nombre_norm:
        for num in range(9, 1, -1):
            if re.search(rf"\b{num}\b", nombre_norm):
                tvg_id = resolver_tvg_id(
                    nombre_norm, nombre_original, f"M+ Liga de Campeones {num}"
                )
                linea = poner_atributo(linea, "tvg-id", tvg_id)
                return poner_atributo(
                    linea,
                    "tvg-logo",
                    f"{PICONS_BASE}/M%2B%20Liga%20de%20Campeones%20{num}.png",
                )
        tvg_id = resolver_tvg_id(
            nombre_norm, nombre_original, "M+ Liga de Campeones HD"
        )
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea,
            "tvg-logo",
            f"{PICONS_BASE}/M%2B%20Liga%20de%20Campeones.png",
        )

    if "HYPERMOTION" in nombre_norm:
        for num in range(10, 1, -1):
            if re.search(rf"\b{num}\b", nombre_norm):
                tvg_id = resolver_tvg_id(
                    nombre_norm, nombre_original, f"LaLiga TV Hypermotion {num}"
                )
                linea = poner_atributo(linea, "tvg-id", tvg_id)
                return poner_atributo(
                    linea,
                    "tvg-logo",
                    f"{PICONS_BASE}/LaLiga%20TV%20Hypermotion%20{num}.png",
                )
        tvg_id = resolver_tvg_id(
            nombre_norm, nombre_original, "LaLiga TV Hypermotion HD"
        )
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea,
            "tvg-logo",
            f"{PICONS_BASE}/LaLiga%20TV%20Hypermotion.png",
        )

    if "DAZN LALIGA" in nombre_norm or "DAZN LA LIGA" in nombre_norm:
        for num in range(10, 1, -1):
            if re.search(rf"\b{num}\b", nombre_norm):
                defecto = f"DAZN LaLiga {num} HD" if num == 2 else f"DAZN LaLiga {num}"
                tvg_id = resolver_tvg_id(nombre_norm, nombre_original, defecto)
                linea = poner_atributo(linea, "tvg-id", tvg_id)
                return poner_atributo(
                    linea,
                    "tvg-logo",
                    f"{PICONS_BASE}/DAZN%20LaLiga%20{num}.png",
                )
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "DAZN LaLiga HD")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea,
            "tvg-logo",
            f"{PICONS_BASE}/DAZN%20LaLiga.png",
        )

    if (
        ("LALIGA" in nombre_norm or "LA LIGA" in nombre_norm)
        and "HYPERMOTION" not in nombre_norm
        and "DAZN" not in nombre_norm
        and "SKY" not in nombre_norm
    ):
        for num in range(10, 1, -1):
            if re.search(rf"\b{num}\b", nombre_norm):
                defecto = f"M+ LaLiga {num} HD" if num == 2 else f"M+ LaLiga {num}"
                tvg_id = resolver_tvg_id(nombre_norm, nombre_original, defecto)
                linea = poner_atributo(linea, "tvg-id", tvg_id)
                return poner_atributo(
                    linea,
                    "tvg-logo",
                    f"{PICONS_BASE}/M%2B%20LaLiga%20{num}.png",
                )
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "M+ LaLiga HD")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea,
            "tvg-logo",
            f"{PICONS_BASE}/M%2B%20LaLiga.png",
        )

    if "VAMOS" in nombre_norm:
        for num in range(10, 1, -1):
            if re.search(rf"\b{num}\b", nombre_norm):
                tvg_id = resolver_tvg_id(
                    nombre_norm, nombre_original, f"M+ Vamos {num}"
                )
                linea = poner_atributo(linea, "tvg-id", tvg_id)
                return poner_atributo(
                    linea,
                    "tvg-logo",
                    f"{PICONS_BASE}/M%2B%20Vamos%20{num}.png",
                )
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "M+ Vamos HD")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea,
            "tvg-logo",
            f"{PICONS_BASE}/M%2B%20Vamos.png",
        )

    if "DAZN" in nombre_norm and not any(
        palabra in nombre_norm
        for palabra in (
            "LALIGA",
            "LA LIGA",
            "F1",
            "FORMULA",
            "MOTOGP",
            "BALONCESTO",
        )
    ):
        for num in range(10, 0, -1):
            if re.search(rf"\b{num}\b", nombre_norm):
                tvg_id = resolver_tvg_id(
                    nombre_norm, nombre_original, f"DAZN {num} HD"
                )
                linea = poner_atributo(linea, "tvg-id", tvg_id)
                return poner_atributo(
                    linea,
                    "tvg-logo",
                    f"{PICONS_BASE}/DAZN%20{num}.png",
                )

    if "EUROSPORT" in nombre_norm:
        for num in range(10, 0, -1):
            if re.search(rf"\b{num}\b", nombre_norm):
                defecto = f"Eurosport {num} HD" if num == 1 else f"Eurosport {num}"
                tvg_id = resolver_tvg_id(nombre_norm, nombre_original, defecto)
                linea = poner_atributo(linea, "tvg-id", tvg_id)
                return poner_atributo(
                    linea,
                    "tvg-logo",
                    f"{PICONS_BASE}/Eurosport%20{num}.png",
                )
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "Eurosport")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea,
            "tvg-logo",
            f"{PICONS_BASE}/Eurosport.png",
        )

    if "DEPORTES" in nombre_norm:
        for num in range(8, 0, -1):
            if re.search(rf"\b{num}\b", nombre_norm):
                defecto = (
                    f"M+ Deportes {num} HD" if num == 2 else f"M+ Deportes {num}"
                )
                tvg_id = resolver_tvg_id(nombre_norm, nombre_original, defecto)
                linea = poner_atributo(linea, "tvg-id", tvg_id)
                return poner_atributo(
                    linea,
                    "tvg-logo",
                    f"{PICONS_BASE}/M%2B%20Deportes%20{num}.png",
                )

    if re.search(r"\bGOLF\s*2\b", nombre_norm):
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "M+ Golf 2 HD")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea, "tvg-logo", f"{PICONS_BASE}/M%2B%20Golf%202.png"
        )
    if "GOLF" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "M+ Golf HD")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(linea, "tvg-logo", f"{PICONS_BASE}/M%2B%20Golf.png")

    if "DAZN BALONCESTO 3" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "DAZN Baloncesto 3")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea, "tvg-logo", f"{PICONS_BASE}/DAZN%20Baloncesto%203.png"
        )
    if "DAZN BALONCESTO 2" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "DAZN Baloncesto 2")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea, "tvg-logo", f"{PICONS_BASE}/DAZN%20Baloncesto%202.png"
        )
    if "DAZN BALONCESTO" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "DAZN Baloncesto")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea, "tvg-logo", f"{PICONS_BASE}/DAZN%20Baloncesto.png"
        )
    if "BALONCESTO" in nombre_norm and "DAZN" not in nombre_norm:
        for num in range(10, 1, -1):
            if re.search(rf"\b{num}\b", nombre_norm):
                tvg_id = resolver_tvg_id(
                    nombre_norm, nombre_original, f"M+ Baloncesto {num}"
                )
                linea = poner_atributo(linea, "tvg-id", tvg_id)
                return poner_atributo(
                    linea,
                    "tvg-logo",
                    f"{PICONS_BASE}/M%2B%20Baloncesto%20{num}.png",
                )
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "M+ Baloncesto")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea, "tvg-logo", f"{PICONS_BASE}/M%2B%20Baloncesto.png"
        )

    if "UFC" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "UFC")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(linea, "tvg-logo", f"{TV_LOGOS_US}/ufc-us.png")
    if "SKY SPORT MOTOGP" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "Sky Sport MotoGP")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea, "tvg-logo", f"{TV_LOGOS_IT}/sky-sport-motogp-hd-it.png"
        )
    if "SKY SPORT TENNIS" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "Sky Sport Tennis")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea, "tvg-logo", f"{TV_LOGOS_IT}/sky-sport-tennis-hd-it.png"
        )
    if "NBA LEAGUE PASS" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "NBA League Pass")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea, "tvg-logo", f"{TV_LOGOS_US}/nba-league-pass-hz-us.png"
        )
    if "NBA ESPN" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "NBA ESPN")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(linea, "tvg-logo", f"{TV_LOGOS_US}/espn-us.png")
    if "ONETORO" in nombre_norm or "ONE TORO" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "Onetoro")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(linea, "tvg-logo", f"{PICONS_BASE}/Onetoro.png")
    if "RFEF" in nombre_norm or "PRIMERA FEDERACION" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "Primera Federación")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea, "tvg-logo", f"{PICONS_BASE}/Primera%20Federaci%C3%B3n.png"
        )
    if re.search(r"\bF1\b", nombre_norm) or "FORMULA 1" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "DAZN F1 HD")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(linea, "tvg-logo", f"{PICONS_BASE}/DAZN%20F1.png")
    if "MOTOGP" in nombre_norm and "SKY" not in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "DAZN MotoGP")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(linea, "tvg-logo", f"{PICONS_BASE}/DAZN%20MotoGP.png")
    if "BEIN SPORTS 3 TR" in nombre_norm or (
        "BEIN SPORTS 3" in nombre_norm and "TR" in nombre_norm
    ):
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "Bein Sports 3 TR")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea, "tvg-logo", "https://i.ibb.co/GkX99sd/Bein3.png"
        )

    if "BEIN SPORTS TR" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "Bein Sports TR")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea, "tvg-logo", "https://i.ibb.co/3fPVPLL/Bein1.png"
        )
    if "BEIN SPORTS 2 TR" in nombre_norm or (
        "BEIN SPORTS 2" in nombre_norm and "TR" in nombre_norm
    ):
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "Bein Sports 2 TR")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://cdn.bein.com/mena/wp-content/uploads/sites/3/2020/06/HD2-1.png",
        )
    if "TENNIS CHANNEL" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "Tennis Channel")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea, "tvg-logo", f"{PICONS_BASE}/Tennis%20Channel.png"
        )
    if "SKY SPORTS LALIGA" in nombre_norm or "SKY SPORTS LA LIGA" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "SKY Sports LaLiga")
        return poner_atributo(linea, "tvg-id", tvg_id)
    if "SPORT TV" in nombre_norm:
        if "3" in nombre_norm:
            tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "Sport TV 3")
            return poner_atributo(linea, "tvg-id", tvg_id)
        if "+" in nombre_norm or "PLUS" in nombre_norm:
            tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "Sport TV+")
            return poner_atributo(linea, "tvg-id", tvg_id)
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "Sport TV")
        return poner_atributo(linea, "tvg-id", tvg_id)

    if "TELEDEPORTE" in nombre_norm or re.search(r"\bTDP\b", nombre_norm):
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "Teledeporte")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(linea, "tvg-logo", f"{PICONS_BASE}/Teledeporte.png")
    if "CUATRO" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "Cuatro HD")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(linea, "tvg-logo", f"{TV_LOGOS_ES}/cuatro-es.png")
    if "TELECINCO" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "Telecinco HD")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(linea, "tvg-logo", f"{TV_LOGOS_ES}/telecinco-es.png")
    if "REAL MADRID TV" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "Real Madrid TV")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(
            linea, "tvg-logo", f"{TV_LOGOS_ES}/real-madrid-tv-es.png"
        )
    if "ESPORT3" in nombre_norm or "ESPORT 3" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "Esport3")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(linea, "tvg-logo", f"{TV_LOGOS_ES}/esport-3-es.png")
    if "A PUNT" in nombre_norm or "APUNT" in nombre_norm:
        tvg_id = resolver_tvg_id(nombre_norm, nombre_original, "À Punt")
        linea = poner_atributo(linea, "tvg-id", tvg_id)
        return poner_atributo(linea, "tvg-logo", f"{TV_LOGOS_ES}/a-punt-es.png")

    k = clave_canal(nombre_original or nombre_norm)
    if k in MAPA_PERSONAL_ID:
        return poner_atributo(linea, "tvg-id", MAPA_PERSONAL_ID[k])

    return linea


def normalizar_linea_personal(linea):
    if not linea.startswith("#EXTINF:") or "," not in linea:
        return linea

    logo_puesto = re.search(r'tvg-logo="([^"]+)"', linea, flags=re.IGNORECASE)
    id_puesto = re.search(r'tvg-id="([^"]+)"', linea, flags=re.IGNORECASE)

    if logo_puesto and id_puesto:
        return linea

    nombre = linea.rsplit(",", 1)[-1].strip()
    nombre_norm = normalizar(nombre)
    sin_sucio = limpiar_logo_si_es_sucio(linea)
    aplicada = aplicar_logo_y_epg(sin_sucio, nombre_norm, nombre)

    if logo_puesto:
        aplicada = poner_atributo(aplicada, "tvg-logo", logo_puesto.group(1))
    if id_puesto:
        aplicada = poner_atributo(aplicada, "tvg-id", id_puesto.group(1))
    return aplicada


# ==========================================================
# LEER Y PROCESAR LOS CANALES DE ELCANO
# ==========================================================

lineas_elcano = fuente_elcano.splitlines()
canales = []

indice = 0

while indice < len(lineas_elcano):
    linea = lineas_elcano[indice].strip()

    if not linea.startswith("#EXTINF:"):
        indice += 1
        continue

    url = None
    siguiente = indice + 1

    while siguiente < len(lineas_elcano):
        candidata = lineas_elcano[siguiente].strip()

        if candidata and not candidata.startswith("#"):
            url = candidata
            break

        siguiente += 1

    if not url:
        indice += 1
        continue

    nombre = linea.rsplit(",", 1)[-1].strip()
    nombre = re.sub(r"\s*\b720p?\b\s*", " ", nombre, flags=re.IGNORECASE)
    nombre = re.sub(r"\s{2,}", " ", nombre).strip()

    if "," in linea:
        prefijo_extinf, _ = linea.rsplit(",", 1)
        linea = f"{prefijo_extinf},{nombre}"
        if re.search(r'tvg-name="[^"]*"', linea, flags=re.IGNORECASE):
            linea = poner_atributo(linea, "tvg-name", nombre)

    nombre_normalizado = normalizar(nombre)

    extinf_mod = aplicar_logo_y_epg(linea, nombre_normalizado, nombre)
    extinf_mod = ajustar_id_con_epg(extinf_mod, nombre)
    extinf_mod = poner_atributo(extinf_mod, "group-title", GROUP_TITLE)

    coincidencia_hash = re.search(r"([0-9a-fA-F]{40})", url)

    if coincidencia_hash:
        hash_id = coincidencia_hash.group(1)
        url_final = "http://127.0.0.1:6878/ace/getstream?id=" + hash_id
    else:
        url_final = url

    canales.append(
        {
            "nombre": nombre,
            "extinf": extinf_mod,
            "url": url_final,
            "indice": len(canales),
        }
    )

    indice = siguiente + 1

if not canales:
    sys.exit(
        "ERROR: Elcano no ha proporcionado canales validos. "
        "No se modifica ningun archivo."
    )

# ==========================================================
# ORDEN SIN ELIMINAR CANALES NI DUPLICADOS
# ==========================================================

canales_ordenados = sorted(canales, key=prioridad_canal)

# ==========================================================
# CONSTRUIR LA ZONA AUTOMATICA
# ==========================================================

bloque_automatico = [
    "# ==========================================",
    "# ZONA AUTOMATICA: ⭐ ELCANO [MÁXIMA CALIDAD]",
    "# ==========================================",
]

for canal in canales_ordenados:
    bloque_automatico.append(canal["extinf"])
    bloque_automatico.append(canal["url"])

texto_nuevo_elcano = salto.join(bloque_automatico)

# ==========================================================
# COMPARAR CANALES PARA EL INFORME
# ==========================================================


def extraer_nombres(texto):
    nombres = set()

    for linea in texto.splitlines():
        if linea.startswith("#EXTINF:") and "," in linea:
            nombres.add(linea.rsplit(",", 1)[-1].strip().upper())

    return nombres


zona_anterior = "".join(lineas_casa[:inicio_personal])

canales_viejos = extraer_nombres(zona_anterior)
canales_new = extraer_nombres(texto_nuevo_elcano)

agregados = sorted(canales_new - canales_viejos)
eliminados = sorted(canales_viejos - canales_new)

timestamp_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

reporte = [
    f"# Resumen de cambios ELCANO - {timestamp_actual}",
    "",
    f"## Canales nuevos ({len(agregados)})",
]

if agregados:
    reporte.extend(f"- {canal}" for canal in agregados)
else:
    reporte.append("- Ninguno.")

reporte.extend(["", f"## Canales eliminados ({len(eliminados)})"])

if eliminados:
    reporte.extend(f"- {canal}" for canal in eliminados)
else:
    reporte.append("- Ninguno.")

(CARPETA_LISTAS / "ultimos_cambios.md").write_text(
    "\n".join(reporte), encoding="utf-8"
)

# ==========================================================
# CABECERA M3U
# ==========================================================
cabecera_m3u = (
    '#EXTM3U url-tvg="https://raw.githubusercontent.com/davidmuma/EPG_dobleM/refs/heads/master/guiatv.xml,'
    'https://epgshare01.online/epgshare01/epg_ripper_US_SPORTS1.xml.gz,'
    'https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz,'
    'https://epgshare01.online/epgshare01/epg_ripper_NL1.xml.gz,'
    'https://epgshare01.online/epgshare01/epg_ripper_PT1.xml.gz,'
    'https://epgshare01.online/epgshare01/epg_ripper_TR1.xml.gz,'
    'https://epgshare01.online/epgshare01/epg_ripper_IT1.xml.gz" '
    'tvg-shift="0" refresh="3600"'
    + salto
    + "#EXTVLCOPT:network-caching=1000"
    + salto
    + '#EXTGRP: group-title=" ELCANO [MÁXIMA CALIDAD]" '
    'group-logo="https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/M%2B%20LaLiga.png"'
    + salto
    + salto
)

# ==========================================================
# MONTAR ARCHIVO CASA Y TAILSCALE
# ==========================================================

cuerpo_personal_limpio = "".join(
    normalizar_linea_personal(linea)
    for linea in cuerpo_personal.splitlines(keepends=True)
    if not re.match(r"^\s*#\s*Ultima sincronizacion:", linea, flags=re.IGNORECASE)
).rstrip("\r\n")

linea_sync = f"{salto}# Ultima sincronizacion: {timestamp_actual}"
cuerpo_personal_con_fecha = cuerpo_personal_limpio + linea_sync

separador = salto + salto

texto_final = (
    cabecera_m3u + texto_nuevo_elcano + separador + cuerpo_personal_con_fecha
)

bloque_tailscale_elcano = texto_nuevo_elcano.replace(
    "127.0.0.1:6878", "100.90.204.66:6878"
)

cuerpo_tailscale_personal = cuerpo_personal_con_fecha.replace(
    "127.0.0.1:6878", "100.90.204.66:6878"
)

texto_tailscale = (
    cabecera_m3u + bloque_tailscale_elcano + separador + cuerpo_tailscale_personal
)

texto_amigos = texto_final

# ==========================================================
# COMPROBACIONES FINALES ANTES DE ESCRIBIR
# ==========================================================

if cuerpo_personal_limpio not in texto_final:
    sys.exit(
        "ERROR: La comprobacion de la zona personal ha fallado. "
        "No se guardan los archivos."
    )

if cuerpo_tailscale_personal not in texto_tailscale:
    sys.exit(
        "ERROR: La zona personal de Tailscale no coincide. "
        "No se guardan los archivos."
    )

if f'tvg-id="{TGV_ID_MOVISTAR_UNIFICADO}"' not in texto_final:
    sys.exit(
        "ERROR: No se ha aplicado el tvg-id unificado a Movistar. "
        "No se guardan los archivos."
    )

# ==========================================================
# GUARDAR ARCHIVOS
# ==========================================================

archivo_casa.write_bytes(texto_final.encode("utf-8"))
archivo_tailscale.write_bytes(texto_tailscale.encode("utf-8"))
archivo_amigos.write_bytes(texto_amigos.encode("utf-8"))

print("==========================================")
print("SINCRONIZACION COMPLETADA CON TAILSCALE")
print("==========================================")
print(f"Canales procesados: {len(canales_ordenados)}")
print(f"Canales nuevos: {len(agregados)}")
print(f"Canales eliminados: {len(eliminados)}")
print("M+ 0 y Movistar Plus unificados con logo moderno y EPG")
print("Onetoro y Primera Federacion configurados")
print("Carpetas personales: adaptadas a Tailscale en Canales m3u")
print("Casa, Tailscale y Amigos: actualizados")
print("==========================================")