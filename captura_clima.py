import requests
import pandas as pd
from datetime import datetime
import os
import re

URL_CLIMA = "https://hipodromosanisidro.com/clima/mb3uv.htm"
BASE_URL_IMG = "https://hipodromosanisidro.com/clima/"
ARCHIVO_CSV = "registro_clima_san_isidro.csv"
CARPETA_GRAFICOS = "graficos"

def capturar_todo():
    ahora = datetime.now()
    try:
        res = requests.get(URL_CLIMA, timeout=20)
        res.encoding = 'latin-1'
        texto = res.text

        # Función de búsqueda por patrón: Busca el número que está antes de una unidad específica
        def extraer(patron_unidad, texto_completo):
            # Busca un número (decimal o entero) que esté cerca de la unidad
            # Ejemplo: "11.1 °C" -> atrapa 11.1
            regex = re.compile(r"(\d+[\.,]?\d*)\s*" + patron_unidad, re.IGNORECASE)
            match = regex.search(texto_completo)
            return match.group(1).replace(',', '.') if match else "0"

        # Extraer dirección del viento (ej: ONO)
        sector = re.search(r"Sector\s+([A-Z]+)", texto)
        viento_dir = sector.group(1) if sector else ""

        registro = {
            "Fecha_Hora": ahora.strftime("%Y-%m-%d %H:%M:%S"),
            "Temperatura_C": extraer("°C", texto),
            "Humedad_pct": extraer("%", texto),
            "Punto_Rocio_C": extraer("°C", texto.split("PUNTO DE ROCIO")[1]) if "PUNTO DE ROCIO" in texto else "0",
            "Presion_hPa": extraer("hPa", texto),
            "Radiacion_Solar_Wm2": extraer("W/m²", texto),
            "Indice_UV": extraer("índice", texto),
            "Viento_Velocidad_kmh": extraer("km/h", texto),
            "Viento_Direccion": viento_dir,
            "Lluvia_Dia_mm": extraer("mm", texto.split("LLUVIA")[1]) if "LLUVIA" in texto else "0",
            "ET_Dia_mm": extraer("mm", texto.split("EVAPOTRANSPIRACION")[1]) if "EVAPOTRANSPIRACION" in texto else "0"
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
