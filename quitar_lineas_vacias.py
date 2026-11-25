from pathlib import Path

archivos = [
    "Canales m3u",
    "Mi lista acestream",
    "lista-amigos",
]

for nombre in archivos:
    archivo = Path(nombre)
    if not archivo.is_file():
        print(f"No encontrado: {nombre}")
        continue

    datos = archivo.read_bytes()
    bom = datos.startswith(b"\xef\xbb\xbf")
    contenido = datos.decode("utf-8-sig")
    lineas = contenido.splitlines(keepends=True)
    limpias = [linea for linea in lineas if linea.strip()]
    resultado = "".join(limpias)
    salida = resultado.encode("utf-8")
    if bom:
        salida = b"\xef\xbb\xbf" + salida
    archivo.write_bytes(salida)
    print(f"Limpiado: {nombre}")
