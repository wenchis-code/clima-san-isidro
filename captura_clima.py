"""
captura_clima.py
Estación Meteorológica - Hipódromo San Isidro
Captura datos numéricos y gráficos desde mb3uv.htm (template Saratoga/Carterlake).
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import os
import re
import sys

# ──────────────────────────────────────────────
# Configuración
# ──────────────────────────────────────────────
URL_BASE   = "https://hipodromosanisidro.com/clima"
URL_PAGINA = f"{URL_BASE}/mb3uv.htm"
CSV_FILE   = "registro_clima_san_isidro.csv"
DIR_GRAFICOS = "graficos"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
}

# Gráficos estándar del template Saratoga/Carterlake mb3uv
# Nombre legible → nombre de archivo en el servidor
GRAFICOS_CONOCIDOS = {
    "temperatura_24h":      "temphum.png",
    "lluvia_24h":           "rain.png",
    "viento_24h":           "wind.png",
    "presion_24h":          "press.png",
    "radiacion_solar_24h":  "solar.png",
    "indice_uv_24h":        "uv.png",
    "et_24h":               "et.png",
    "resumen_diario":       "summary.gif",
    "rosa_vientos":         "windrose.png",
    "temperatura_mes":      "tempmon.png",
    "lluvia_mes":           "rainmon.png",
    "viento_mes":           "windmon.png",
    "temperatura_anual":    "tempyear.png",
    "lluvia_anual":         "rainyear.png",
}


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def fetch_html(url: str) -> str | None:
    """Descarga una URL con reintentos. Retorna el texto o None."""
    for intento in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            r.encoding = "latin-1"
            return r.text
        except requests.RequestException as e:
            print(f"  [reintento {intento+1}/3] Error fetching {url}: {e}")
    return None


def extraer_numero(soup: BeautifulSoup, label: str, unidad: str) -> str:
    """
    Busca en el BeautifulSoup el primer número asociado a una etiqueta
    y una unidad. Retorna el valor como string o '' si no se encuentra.
    Estrategia: buscar el texto del label, subir al bloque tabla/td/tr,
    y buscar el patrón numérico+unidad.
    """
    # Buscar el texto del label en cualquier elemento
    el = soup.find(string=re.compile(re.escape(label), re.IGNORECASE))
    if not el:
        return ""

    # Subir hasta encontrar un contenedor semántico (tr, td, div, table)
    contenedor = el.parent
    for _ in range(6):
        if contenedor is None:
            break
        texto = contenedor.get_text(" ", strip=True)
        # Buscar patrón número + unidad
        unidad_re = re.escape(unidad)
        match = re.search(r"([\d]+[.,]?\d*)\s*" + unidad_re, texto)
        if match:
            return match.group(1).replace(",", ".")
        contenedor = contenedor.parent

    return ""


def extraer_direccion_viento(soup: BeautifulSoup) -> str:
    """Extrae la dirección del viento (N, NE, S, etc.) del HTML."""
    # Buscar el bloque VIENTO
    el = soup.find(string=re.compile(r"VIENTO", re.IGNORECASE))
    if not el:
        return ""

    contenedor = el.parent
    for _ in range(8):
        if contenedor is None:
            break
        texto = contenedor.get_text(" ", strip=True)
        # Buscar "Sector XXX" o "Dirección: XXX"
        match = re.search(r"Sector\s+([A-Z]{1,3})", texto)
        if match:
            return match.group(1)
        # Buscar dirección cardinal como palabra suelta (ej: "NNO", "ESE")
        match = re.search(
            r"\b(N|NNE|NE|ENE|E|ESE|SE|SSE|S|SSO|SO|OSO|O|ONO|NO|NNO)\b",
            texto
        )
        if match:
            return match.group(1)
        contenedor = contenedor.parent

    return ""


# ──────────────────────────────────────────────
# Captura de datos
# ──────────────────────────────────────────────

def capturar_datos(html: str) -> dict:
    """Parsea el HTML y extrae todas las variables meteorológicas."""
    soup = BeautifulSoup(html, "html.parser")

    datos = {
        "Fecha_Hora":              datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Temperatura_C":           extraer_numero(soup, "TEMPERATURA",          "°C"),
        "Humedad_pct":             extraer_numero(soup, "HUMEDAD",               "%"),
        "Punto_Rocio_C":           extraer_numero(soup, "PUNTO DE ROCIO",        "°C"),
        "Presion_hPa":             extraer_numero(soup, "PRESION BAROMETRICA",   "hPa"),
        "Radiacion_Solar_Wm2":     extraer_numero(soup, "RADIACION SOLAR",       "W/m²"),
        "Indice_UV":               extraer_numero(soup, "RADIACION UV",          "índice"),
        "Viento_Velocidad_kmh":    extraer_numero(soup, "VIENTO",                "km/h"),
        "Viento_Direccion":        extraer_direccion_viento(soup),
        "Lluvia_Dia_mm":           extraer_numero(soup, "LLUVIA",                "mm"),
        "ET_Dia_mm":               extraer_numero(soup, "EVAPOTRANSPIRACION",    "mm"),
    }

    # Validar: si todos los valores numéricos quedaron vacíos, avisar
    valores = [v for k, v in datos.items() if k != "Fecha_Hora" and k != "Viento_Direccion"]
    if all(v == "" for v in valores):
        print("  ADVERTENCIA: No se extrajeron datos numéricos. "
              "Puede que la estructura HTML haya cambiado.")

    return datos


# ──────────────────────────────────────────────
# Descarga de gráficos
# ──────────────────────────────────────────────

def descubrir_graficos_en_html(html: str) -> list[str]:
    """
    Analiza el HTML para encontrar imágenes adicionales no listadas
    en GRAFICOS_CONOCIDOS (ej: gráficos con timestamp en el nombre).
    Retorna lista de URLs absolutas.
    """
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src:
            continue
        # Solo imágenes que parezcan gráficos (no iconos UI)
        if re.search(r"\.(png|gif|jpg)$", src, re.IGNORECASE):
            if not src.startswith("http"):
                src = f"{URL_BASE}/{src.lstrip('/')}"
            urls.append(src)
    return list(dict.fromkeys(urls))  # deduplicar manteniendo orden


def descargar_graficos(html: str):
    """
    Descarga todos los gráficos conocidos + los descubiertos en el HTML.
    Guarda en DIR_GRAFICOS/ con nombres descriptivos.
    """
    os.makedirs(DIR_GRAFICOS, exist_ok=True)
    descargados = []
    fallidos = []

    # 1. Gráficos conocidos del template
    for nombre_local, archivo_remoto in GRAFICOS_CONOCIDOS.items():
        url = f"{URL_BASE}/{archivo_remoto}"
        destino = os.path.join(DIR_GRAFICOS, f"{nombre_local}.{archivo_remoto.split('.')[-1]}")
        ok = _descargar_imagen(url, destino)
        if ok:
            descargados.append(nombre_local)
        else:
            fallidos.append(nombre_local)

    # 2. Gráficos descubiertos dinámicamente en el HTML
    urls_html = descubrir_graficos_en_html(html)
    archivos_conocidos = set(GRAFICOS_CONOCIDOS.values())

    for url in urls_html:
        filename = url.split("/")[-1].split("?")[0]
        if filename in archivos_conocidos:
            continue  # ya descargado arriba
        if re.search(r"(icon|logo|btn|arrow|bg|flag)", filename, re.IGNORECASE):
            continue  # probablemente UI, no datos
        destino = os.path.join(DIR_GRAFICOS, filename)
        ok = _descargar_imagen(url, destino)
        if ok:
            descargados.append(filename)
        else:
            fallidos.append(filename)

    print(f"  Gráficos descargados: {len(descargados)}")
    if fallidos:
        print(f"  Gráficos no encontrados en servidor: {len(fallidos)} "
              f"({', '.join(fallidos[:5])}{'...' if len(fallidos) > 5 else ''})")

    return descargados


def _descargar_imagen(url: str, destino: str) -> bool:
    """Descarga una imagen. Retorna True si tuvo éxito."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200 and len(r.content) > 100:
            with open(destino, "wb") as f:
                f.write(r.content)
            return True
        return False
    except requests.RequestException:
        return False


# ──────────────────────────────────────────────
# CSV
# ──────────────────────────────────────────────

def guardar_csv(datos: dict):
    """Agrega una fila al CSV acumulativo."""
    df = pd.DataFrame([datos])
    escribir_header = not os.path.exists(CSV_FILE)
    df.to_csv(
        CSV_FILE,
        mode="a",
        header=escribir_header,
        index=False,
        encoding="utf-8-sig",
    )
    print(f"  CSV actualizado: {CSV_FILE}")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def capturar():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando captura...")

    html = fetch_html(URL_PAGINA)
    if html is None:
        print("ERROR FATAL: No se pudo descargar la página. Abortando.")
        sys.exit(1)

    print("  Página descargada correctamente.")

    # Datos numéricos
    datos = capturar_datos(html)
    guardar_csv(datos)
    print(f"  Temperatura: {datos['Temperatura_C']}°C | "
          f"Humedad: {datos['Humedad_pct']}% | "
          f"Lluvia día: {datos['Lluvia_Dia_mm']}mm | "
          f"Viento: {datos['Viento_Velocidad_kmh']} km/h {datos['Viento_Direccion']}")

    # Gráficos
    print("  Descargando gráficos...")
    descargar_graficos(html)

    print("  ✓ Captura completa.")


if __name__ == "__main__":
    capturar()
