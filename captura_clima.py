import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import re

URL_CLIMA = "https://hipodromosanisidro.com/clima/mb3uv.htm"
BASE_URL_IMG = "https://hipodromosanisidro.com/clima/"
ARCHIVO_CSV = "registro_clima_san_isidro.csv"
CARPETA_GRAFICOS = "graficos"

def limpiar(valor):
    if not valor: return ""
    # Se queda solo con números y puntos decimales
    res = re.search(r"[-+]?\d*\.\d+|\d+", valor.replace(',', '.'))
    return res.group() if res else ""

def capturar_todo():
    ahora = datetime.now()
    try:
        res = requests.get(URL_CLIMA, timeout=20)
        res.encoding = 'latin-1'
        soup = BeautifulSoup(res.text, 'html.parser')

        # Esta función busca el texto que está inmediatamente después de una palabra clave
        def buscar_dato(texto_buscado):
            elemento = soup.find(string=re.compile(texto_buscado, re.IGNORECASE))
            if elemento:
                # Buscamos en la celda de al lado (td) o en el contenedor siguiente
                parent_td = elemento.find_parent('td')
                if parent_td:
                    siguiente_td = parent_td.find_next_sibling('td')
                    if siguiente_td:
                        return siguiente_td.get_text(strip=True)
            return ""

        registro = {
            "Fecha_Hora": ahora.strftime("%Y-%m-%d %H:%M:%S"),
            "Temperatura_C": limpiar(buscar_dato("Actual")),
            "Humedad_pct": limpiar(buscar_dato("HUMEDAD")),
            "Punto_Rocio_C": limpiar(buscar_dato("PUNTO DE ROCIO")),
            "Presion_hPa": limpiar(buscar_dato("BAROMETRO")),
            "Radiacion_Solar_Wm2": limpiar(buscar_dato("RADIACION SOLAR")),
            "Indice_UV": limpiar(buscar_dato("INDICE UV")),
            "Viento_Velocidad_kmh": limpiar(buscar_dato("VIENTO")),
            "Viento_Direccion": buscar_dato("VIENTO").split()[-1] if buscar_dato("VIENTO") else "",
            "Lluvia_Dia_mm": limpiar(buscar_dato("LLUVIA DIARIA")),
            "ET_Dia_mm": limpiar(buscar_dato("EVAPOTRANSPIRACION"))
        }

        # Guardar en CSV
        df = pd.DataFrame([registro])
        df.to_csv(ARCHIVO_CSV, mode='a', index=False, header=not os.path.exists(ARCHIVO_CSV), encoding='utf-8-sig')
        print(f"Captura exitosa: {registro['Temperatura_C']} C")

        # Gráficos (Solo a las 23hs)
        if ahora.hour == 23:
            if not os.path.exists(CARPETA_GRAFICOS): os.makedirs(CARPETA_GRAFICOS)
            for g in ["temp.gif", "hum.gif", "baro.gif", "wind.gif", "rain.gif", "uv.gif", "solar.gif"]:
                try:
                    r_img = requests.get(BASE_URL_IMG + g, timeout=10)
                    with open(f"{CARPETA_GRAFICOS}/{ahora.strftime('%Y%m%d')}_{g}", 'wb') as f:
                        f.write(r_img.content)
                except: continue

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    capturar_todo()
