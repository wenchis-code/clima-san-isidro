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

def extraer_numero(texto):
    if not texto: return "0"
    # Busca el primer número (entero o decimal)
    match = re.search(r"[-+]?\d*\.\d+|\d+", texto.replace(',', '.'))
    return match.group() if match else "0"

def capturar_todo():
    ahora = datetime.now()
    try:
        res = requests.get(URL_CLIMA, timeout=20)
        res.encoding = 'windows-1252'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Obtenemos todo el texto de la página de forma plana
        todo_el_texto = soup.get_text(" ", strip=True)

        # Diccionario de búsqueda inteligente: "Palabra clave": "Lo que encontramos"
        # Usamos expresiones regulares para buscar el número que sigue a la palabra
        def buscar_valor(etiqueta, patron=r"(\d+[\.,]?\d*)"):
            # Busca la etiqueta y captura el primer número que aparezca después
            regex = re.compile(re.escape(etiqueta) + r".*?" + patron, re.IGNORECASE | re.DOTALL)
            match = regex.search(todo_el_texto)
            return match.group(1) if match else "0"

        # Captura de datos usando el texto plano (más robusto que las tablas)
        registro = {
            "Fecha_Hora": ahora.strftime("%Y-%m-%d %H:%M:%S"),
            "Temperatura_C": extraer_numero(buscar_valor("Actual")), 
            "Humedad_pct": extraer_numero(buscar_valor("HUMEDAD Actual")),
            "Punto_Rocio_C": extraer_numero(buscar_valor("PUNTO DE ROCIO Actual")),
            "Presion_hPa": extraer_numero(buscar_valor("PRESION BAROMETRICA Actual")),
            "Radiacion_Solar_Wm2": extraer_numero(buscar_valor("RADIACION SOLAR Actual")),
            "Indice_UV": extraer_numero(buscar_valor("RADIACION UV Actual")),
            "Viento_Velocidad_kmh": extraer_numero(buscar_valor("Velocidad")),
            "Viento_Direccion": re.search(r"Sector\s+([A-Z]+)", todo_el_texto).group(1) if re.search(r"Sector\s+([A-Z]+)", todo_el_texto) else "",
            "Lluvia_Dia_mm": extraer_numero(buscar_valor("LLUVIA Diaria")),
            "ET_Dia_mm": extraer_numero(buscar_valor("EVAPOTRANSPIRACION Diaria"))
        }

        # Guardar en CSV
        df = pd.DataFrame([registro])
        df.to_csv(ARCHIVO_CSV, mode='a', index=False, header=not os.path.exists(ARCHIVO_CSV), encoding='utf-8-sig')
        print(f"Captura exitosa: {registro}")

        # Gráficos (Solo a las 23hs)
        if ahora.hour == 23:
            if not os.path.exists(CARPETA_GRAFICOS): os.makedirs(CARPETA_GRAFICOS)
            imgs = ["OutsideTempHistory.gif", "OutsideHumidityHistory.gif", "BarometerHistory.gif", "WindSpeedHistory.gif", "RainHistory.gif", "SolarRadHistory.gif", "UVHistory.gif"]
            for g in imgs:
                try:
                    r_img = requests.get(BASE_URL_IMG + g, timeout=10)
                    with open(f"{CARPETA_GRAFICOS}/{ahora.strftime('%Y%m%d')}_{g}", 'wb') as f:
                        f.write(r_img.content)
                except: continue

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    capturar_todo()
