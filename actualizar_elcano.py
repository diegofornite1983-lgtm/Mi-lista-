import datetime
import re
import sys
import unicodedata
import urllib.request
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
# FUNCIONES AUXILIARES
# ==========================================================


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caracter for caracter in texto if unicodedata.category(caracter) != "Mn"
    )
    return texto.upper().strip()


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

    # 1. Movistar Plus clasico (arriba del todo).
    if nombre.startswith("MOVISTAR PLUS") or nombre.startswith("MOVISTAR+"):
        return (0, 0, calidad, canal["indice"])

    # 2. M+ 0: justo debajo del ultimo Movistar Plus, antes de la Champions.
    if re.search(r"\bM\+\s*0\b", nombre):
        return (1, 0, calidad, canal["indice"])

    # 3. LaLiga y sus multis (excluyendo Hypermotion).
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

    # 4. Liga de Campeones, del 1 al 8.
    if "CAMPEONES" in nombre or "CHAMPIONS" in nombre:
        return (3, numero, calidad, canal["indice"])

    # 5. Movistar Deportes: principal y del 2 al 8 juntos.
    if "DEPORTES" in nombre and "BALONCESTO" not in nombre:
        return (4, numero, calidad, canal["indice"])

    # 6. DAZN F1 y DAZN MotoGP.
    if "F1" in nombre or "FORMULA 1" in nombre:
        return (5, 0, calidad, canal["indice"])

    if "MOTOGP" in nombre:
        return (5, 1, calidad, canal["indice"])

    # 7. DAZN generales: del 1 al 4.
    if "DAZN" in nombre and not any(
        palabra in nombre
        for palabra in ("F1", "FORMULA", "MOTOGP", "LALIGA", "BALONCESTO")
    ):
        return (6, numero, calidad, canal["indice"])

    # 8. M+ Vamos.
    if "VAMOS" in nombre:
        return (7, 0, numero, calidad, canal["indice"])

    # 9. LaLiga Hypermotion (Segunda division).
    if "HYPERMOTION" in nombre:
        return (8, 0, numero, calidad, canal["indice"])

    # 10. Primera Federacion / RFEF (Justo debajo de la Hypermotion).
    if "RFEF" in nombre or "PRIMERA FEDERACION" in nombre:
        return (9, 0, nombre, calidad, canal["indice"])

    # 11. Golf, Eurosport, Tenis y Sport TV.
    if "GOLF" in nombre:
        return (10, 0, numero, calidad, canal["indice"])

    if "EUROSPORT" in nombre:
        return (10, 1, numero, calidad, canal["indice"])

    if "TENIS" in nombre or "TENNIS" in nombre:
        return (10, 2, numero, calidad, canal["indice"])

    if "SPORT TV" in nombre:
        return (10, 3, numero, calidad, canal["indice"])

    # 12. Otros canales generales de deportes y variados de Elcano.
    if (
        "BALONCESTO" not in nombre
        and not nombre.startswith("NBA")
        and not es_tdt_abierto(nombre)
    ):
        return (11, 0, nombre, calidad, canal["indice"])

    # 13. Baloncesto y NBA (Abajo del todo, antes de la TDT).
    if "BALONCESTO" in nombre or nombre.startswith("NBA"):
        return (12, numero, calidad, canal["indice"])

    # 14. TDT y canales abiertos (Al final absoluto).
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


# Logo oscuro base para cualquier canal que no tenga regla propia
URL_LOGO_OSCURO_BASE = "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/Movistar%20Plus.png"


def aplicar_logo_y_epg(linea, nombre_norm):
    linea = limpiar_logo_si_es_sucio(linea)

    # M+ 0 y Movistar Plus clasico: logotipo y EPG unificada
    if re.search(r"\bM\+\s*0\b", nombre_norm) or (
        nombre_norm.startswith("MOVISTAR PLUS") or nombre_norm.startswith("MOVISTAR+")
    ):
        return limpiar_y_forzar_movistar(linea)

    # DAZN LaLiga (numerados del 10 al 2 y principal)
    if "DAZN LALIGA" in nombre_norm or "DAZN LA LIGA" in nombre_norm:
        for num in range(10, 1, -1):
            if re.search(rf"\b{num}\b", nombre_norm):
                linea = poner_atributo(linea, "tvg-id", f"DAZN LaLiga {num}")
                return poner_atributo(
                    linea,
                    "tvg-logo",
                    f"https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/DAZN%20LaLiga%20{num}.png",
                )
        linea = poner_atributo(linea, "tvg-id", "DAZN LaLiga")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/DAZN%20LaLiga.png",
        )

    # M+ LaLiga / LaLiga (excluyendo Hypermotion y DAZN)
    if (
        ("LALIGA" in nombre_norm or "LA LIGA" in nombre_norm)
        and "HYPERMOTION" not in nombre_norm
        and "DAZN" not in nombre_norm
    ):
        for num in range(10, 1, -1):
            if re.search(rf"\b{num}\b", nombre_norm):
                linea = poner_atributo(linea, "tvg-id", f"M+ LaLiga {num}")
                return poner_atributo(
                    linea,
                    "tvg-logo",
                    f"https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/M%2B%20LaLiga%20{num}.png",
                )
        linea = poner_atributo(linea, "tvg-id", "M+ LaLiga")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/M%2B%20LaLiga.png",
        )

    # LaLiga Hypermotion numerados (2 al 10)
    if "HYPERMOTION" in nombre_norm:
        for num in range(10, 1, -1):
            if re.search(rf"\b{num}\b", nombre_norm):
                linea = poner_atributo(linea, "tvg-id", f"LaLiga TV Hypermotion {num}")
                return poner_atributo(
                    linea,
                    "tvg-logo",
                    f"https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/LaLiga%20TV%20Hypermotion%20{num}.png",
                )

    # Liga de Campeones del 5 al 9
    if "CAMPEONES" in nombre_norm or "CHAMPIONS" in nombre_norm:
        for num in range(5, 10):
            if re.search(rf"\b{num}\b", nombre_norm):
                linea = poner_atributo(linea, "tvg-id", f"M+ Liga de Campeones {num}")
                return poner_atributo(
                    linea,
                    "tvg-logo",
                    f"https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/M%2B%20Liga%20de%20Campeones%20{num}.png",
                )

    # DAZN F1 y MotoGP
    if "SKY SPORT MOTOGP" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "Sky Sport MotoGP")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/hd/sky-sport-motogp-hd-it.png",
        )

    if "F1" in nombre_norm or "FORMULA 1" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "DAZN F1 HD")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/DAZN%20F1.png",
        )

    if "MOTOGP" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "DAZN MotoGP")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/DAZN%20MotoGP.png",
        )

    # DAZN generales del 3 al 10
    if "DAZN" in nombre_norm and not any(
        palabra in nombre_norm
        for palabra in ("LALIGA", "LA LIGA", "F1", "FORMULA", "MOTOGP", "BALONCESTO")
    ):
        for num in range(10, 2, -1):
            if re.search(rf"\b{num}\b", nombre_norm):
                linea = poner_atributo(linea, "tvg-id", f"DAZN {num} HD")
                return poner_atributo(
                    linea,
                    "tvg-logo",
                    f"https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/DAZN%20{num}.png",
                )

    # M+ Vamos
    if "VAMOS" in nombre_norm:
        for num in range(10, 3, -1):
            if re.search(rf"\b{num}\b", nombre_norm):
                linea = poner_atributo(linea, "tvg-id", f"M+ Vamos {num}")
                return poner_atributo(
                    linea,
                    "tvg-logo",
                    f"https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/M%2B%20Vamos%20{num}.png",
                )
        for num in range(10, 1, -1):
            if re.search(rf"\b{num}\b", nombre_norm):
                linea = poner_atributo(linea, "tvg-id", f"M+ Vamos {num}")
                return poner_atributo(linea, "tvg-logo", "https://i.ibb.co/gWMRpFB/vamos.png")
        linea = poner_atributo(linea, "tvg-id", "M+ Vamos HD")
        return poner_atributo(linea, "tvg-logo", "https://i.ibb.co/gWMRpFB/vamos.png")

    # Deportes 6 y 7
    if re.search(r"\bDEPORTES\s*6\b", nombre_norm):
        linea = poner_atributo(linea, "tvg-id", "M+ Deportes 6")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/M%2B%20Deportes%206.png",
        )

    if re.search(r"\bDEPORTES\s*7\b", nombre_norm):
        linea = poner_atributo(linea, "tvg-id", "M+ Deportes 7")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/M%2B%20Deportes%207.png",
        )

    # Golf
    if re.search(r"\bGOLF\s*2\b", nombre_norm):
        linea = poner_atributo(linea, "tvg-id", "M+ Golf 2 HD")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/M%2B%20Golf%202.png",
        )

    if "GOLF" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "M+ Golf HD")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/M%2B%20Golf.png",
        )

    # Baloncesto
    if "DAZN BALONCESTO 3" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "DAZN Baloncesto 3")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/DAZN%20Baloncesto%203.png",
        )

    if "DAZN BALONCESTO 2" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "DAZN Baloncesto 2")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/DAZN%20Baloncesto%202.png",
        )

    if "DAZN BALONCESTO" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "DAZN Baloncesto")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/DAZN%20Baloncesto.png",
        )

    if "BALONCESTO" in nombre_norm and "DAZN" not in nombre_norm:
        for num in range(10, 3, -1):
            if re.search(rf"\b{num}\b", nombre_norm):
                linea = poner_atributo(linea, "tvg-id", f"M+ Baloncesto {num}")
                return poner_atributo(
                    linea,
                    "tvg-logo",
                    f"https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/M%2B%20Baloncesto%20{num}.png",
                )

    if re.search(r"\bBALONCESTO\s*3\b", nombre_norm):
        linea = poner_atributo(linea, "tvg-id", "M+ Baloncesto 3")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/M%2B%20Baloncesto%203.png",
        )

    if re.search(r"\bBALONCESTO\s*2\b", nombre_norm):
        linea = poner_atributo(linea, "tvg-id", "M+ Baloncesto 2")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/M%2B%20Baloncesto%202.png",
        )

    if "BALONCESTO" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "M+ Baloncesto")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/M%2B%20Baloncesto.png",
        )

    # Otros canales con logo/ID
    if "UFC" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "UFC")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-states/ufc-us.png",
        )

    if "SKY SPORT TENNIS" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "Sky Sport Tennis")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/hd/sky-sport-tennis-hd-it.png",
        )

    if "TENNIS CHANNEL" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "Tennis Channel")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/Tennis%20Channel.png",
        )

    if "BEIN SPORTS 3 TR" in nombre_norm or ("BEIN SPORTS 3" in nombre_norm and "TR" in nombre_norm):
        linea = poner_atributo(linea, "tvg-id", "Bein Sports 3 TR")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/turkey/bein-sports-haber-tr.png",
        )

    if "BEIN SPORTS TR" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "Bein Sports TR")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/tv-logo/tv-logos/refs/heads/main/countries/turkey/bein-sports-haber-tr.png",
        )

    if "NBA LEAGUE PASS" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "NBA League Pass")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/tv-logo/tv-logos/refs/heads/main/countries/united-states/nba-league-pass-hz-us.png",
        )

    if "NBA ESPN" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "NBA ESPN")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/tv-logo/tv-logos/refs/heads/main/countries/united-states/espn-us.png",
        )

    if "ONETORO" in nombre_norm or "ONE TORO" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "Onetoro")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/Onetoro.png",
        )

    if "RFEF" in nombre_norm or "PRIMERA FEDERACION" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "Primera Federación")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/Primera%20Federaci%C3%B3n.png",
        )

    if "EUROSPORT" in nombre_norm:
        for num in range(10, 0, -1):
            if re.search(rf"\b{num}\b", nombre_norm):
                linea = poner_atributo(linea, "tvg-id", f"Eurosport {num}")
                return poner_atributo(
                    linea,
                    "tvg-logo",
                    f"https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/Eurosport%20{num}.png",
                )
        linea = poner_atributo(linea, "tvg-id", "Eurosport")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/Eurosport.png",
        )

    if "CUATRO" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "Cuatro HD")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/spain/cuatro-es.png",
        )

    if "TELECINCO" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "Telecinco HD")
        return poner_atributo(linea, "tvg-logo", "https://i.ibb.co/81wJ3GH/telecinco.png")

    if "REAL MADRID TV" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "Real Madrid TV")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/spain/real-madrid-tv-es.png",
        )

    if "ESPORT3" in nombre_norm or "ESPORT 3" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "Esport 3")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/spain/esport3-es.png",
        )

    if "A PUNT" in nombre_norm or "APUNT" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "À Punt")
        return poner_atributo(
            linea,
            "tvg-logo",
            "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/spain/a-punt-es.png",
        )

    if "SKY SPORTS LALIGA" in nombre_norm or "SKY SPORTS LA LIGA" in nombre_norm:
        linea = poner_atributo(linea, "tvg-id", "SKY Sports LaLiga")
        return poner_atributo(linea, "tvg-logo", URL_LOGO_OSCURO_BASE)

    if "SPORT TV" in nombre_norm:
        if "3" in nombre_norm:
            linea = poner_atributo(linea, "tvg-id", "Sport TV 3")
        elif "+" in nombre_norm or "PLUS" in nombre_norm:
            linea = poner_atributo(linea, "tvg-id", "Sport TV+")
        else:
            linea = poner_atributo(linea, "tvg-id", "Sport TV")
        return poner_atributo(linea, "tvg-logo", URL_LOGO_OSCURO_BASE)

    # Cualquier otro canal: aplica el logo oscuro base para que todos queden uniformes
    return poner_atributo(linea, "tvg-logo", URL_LOGO_OSCURO_BASE)




def normalizar_linea_personal(linea):
    if not linea.startswith("#EXTINF:") or "," not in linea:
        return linea
    nombre = linea.rsplit(",", 1)[-1].strip()
    nombre_norm = normalizar(nombre)
    sin_sucio = limpiar_logo_si_es_sucio(linea)
    logo_match = re.search(r'tvg-logo="([^"]+)"', sin_sucio, flags=re.IGNORECASE)
    id_match = re.search(r'tvg-id="([^"]+)"', sin_sucio, flags=re.IGNORECASE)
    if logo_match and id_match:
        return sin_sucio
    aplicada = aplicar_logo_y_epg(sin_sucio, nombre_norm)
    if logo_match:
        aplicada = poner_atributo(aplicada, "tvg-logo", logo_match.group(1))
    if id_match:
        aplicada = poner_atributo(aplicada, "tvg-id", id_match.group(1))
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
    nombre_normalizado = normalizar(nombre)

    extinf_mod = aplicar_logo_y_epg(linea, nombre_normalizado)
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
    "#EXTM3U url-tvg="
    '"https://raw.githubusercontent.com/davidmuma/EPG_dobleM/refs/heads/master/guiatv.xml,'
    "https://epgshare01.online/epgshare01/epg_ripper_NL1.xml.gz,"
    'https://raw.githubusercontent.com/davidmuma/EPG_dobleM/master/guiatv.xml" '
    'refresh="3600"'
    + salto
    + "#EXTVLCOPT:network-caching=1000"
    + salto
    + '#EXTGRP: group-title="⭐ ELCANO [MÁXIMA CALIDAD]" '
    'group-logo="https://raw.githubusercontent.com/davidmuma/picons_dobleM/master/icon/M%2B%20LaLiga.png"'
    + salto
    + salto
)

# ==========================================================
# MONTAR ARCHIVO CASA (Mantiene IP local 127.0.0.1 abajo)
# ==========================================================

cuerpo_personal_limpio = "".join(
    normalizar_linea_personal(linea)
    for linea in cuerpo_personal.splitlines(keepends=True)
)

separador = salto + salto

texto_final = (
    cabecera_m3u + texto_nuevo_elcano + separador + cuerpo_personal_limpio
)

# ==========================================================
# MONTAR ARCHIVO TAILSCALE (CAMBIA LA IP ARRIBA Y ABAJO)
# ==========================================================

bloque_tailscale_elcano = texto_nuevo_elcano.replace(
    "127.0.0.1:6878", "100.90.204.66:6878"
)

cuerpo_tailscale_personal = cuerpo_personal_limpio.replace(
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