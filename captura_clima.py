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
    if not valor: return "0"
    # Extrae solo números y puntos
    res = re.search(r"[-+]?\d*\.\d+|\d+", valor.replace(',', '.'))
    return res.group() if res else "0"

def capturar_todo():
    ahora = datetime.now()
    try:
        res = requests.get(URL_CLIMA, timeout=20)
        res.encoding = 'windows-1252' # La codificación exacta de la página
        soup = BeautifulSoup(res.text, 'html.parser')

        # Extraemos todos los textos de las celdas para buscarlos
        celdas = [c.get_text(strip=True) for c in soup.find_all('td')]

        # Función para buscar un valor que está después de una etiqueta
        def encontrar(etiqueta, lista):
            try:
                idx = lista.index(etiqueta)
                return lista[idx + 1]
            except:
                return ""

        # Mapeo manual basado en el HTML que me pasaste
        registro = {
            "Fecha_Hora": ahora.strftime("%Y-%m-%d %H:%M:%S"),
            "Temperatura_C": limpiar(encontrar("Actual", celdas)),
            "Humedad_pct": limpiar(celdas[celdas.index("HUMEDAD")+4]), # Salto específico para humedad
            "Punto_Rocio_C": limpiar(celdas[celdas.index("PUNTO DE ROCIO")+4]),
            "Presion_hPa": limpiar(celdas[celdas.index("PRESION BAROMETRICA")+4]),
            "Radiacion_Solar_Wm2": limpiar(celdas[celdas.index("RADIACION SOLAR")+4]),
            "Indice_UV": limpiar(celdas[celdas.index("RADIACION UV")+4]),
            "Viento_Velocidad_kmh": limpiar(celdas[celdas.index("VIENTO")+5]),
            "Viento_Direccion": celdas[celdas.index("VIENTO")+7].split('(')[0].strip(),
            "Lluvia_Dia_mm": limpiar(celdas[celdas.index("LLUVIA")+4]),
            "ET_Dia_mm": limpiar(celdas[celdas.index("ET - EVAPOTRANSPIRACION")+2])
        }

        # Guardar en CSV
        df = pd.DataFrame([registro])
        df.to_csv(ARCHIVO_CSV, mode='a', index=False, header=not os.path.exists(ARCHIVO_CSV), encoding='utf-8-sig')
        print(f"¡Captura exitosa! Temp: {registro['Temperatura_C']}°C")

        # Gráficos (Solo a las 23hs)
        if ahora.hour == 23:
            if not os.path.exists(CARPETA_GRAFICOS): os.makedirs(CARPETA_GRAFICOS)
            for g in ["OutsideTempHistory.gif", "OutsideHumidityHistory.gif", "BarometerHistory.gif", "WindSpeedHistory.gif", "RainHistory.gif", "SolarRadHistory.gif", "UVHistory.gif"]:
                try:
                    r_img = requests.get(BASE_URL_IMG + g, timeout=10)
                    with open(f"{CARPETA_GRAFICOS}/{ahora.strftime('%Y%m%d')}_{g}", 'wb') as f:
                        f.write(r_img.content)
                except: continue

    except Exception as e:
        print(f"Error crítico: {e}")

if __name__ == "__main__":
    capturar_todo()
