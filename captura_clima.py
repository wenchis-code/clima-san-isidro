import requests
import pandas as pd
from datetime import datetime
import os
import re

def capturar():
    url = "https://hipodromosanisidro.com/clima/mb3uv.htm"
    archivo = "registro_clima_san_isidro.csv"
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        res = requests.get(url, timeout=30)
        res.encoding = 'windows-1252'
        html = res.text

        # 1. Limpiamos las etiquetas HTML y las entidades molestas
        html_limpio = re.sub(r'<[^>]*>', ' ', html).replace('&nbsp;', ' ')

        # 2. Función extractora a prueba de espacios ocultos
        def extraer(patron):
            # re.S permite que el buscador ignore los saltos de línea
            match = re.search(patron, html_limpio, re.IGNORECASE | re.DOTALL)
            if match:
                val = match.group(1).replace(',', '.')
                return re.sub(r'[^0-9.]', '', val)
            return "0"

        # 3. Mapeo a medida (probado con el HTML real)
        m_dir = re.search(r"Sector\s+([A-Z]+)", html_limpio)
        
        datos = {
            "Fecha_Hora": ahora,
            "Temperatura_C": extraer(r"TEMPERATURA.*?Actual\s*([\d\.,]+)\s*°C"),
            "Humedad_pct": extraer(r"HUMEDAD.*?Actual\s*([\d\.,]+)\s*%"),
            "Punto_Rocio_C": extraer(r"PUNTO\s+DE\s+ROCIO.*?Actual\s*([\d\.,]+)\s*°C"),
            "Presion_hPa": extraer(r"PRESION\s+BAROMETRICA.*?Actual\s*([\d\.,]+)\s*hPa"),
            "Radiacion_Solar_Wm2": extraer(r"RADIACION\s+SOLAR.*?Actual\s*([\d\.,]+)\s*W/m"),
            "Indice_UV": extraer(r"RADIACION\s+UV.*?Actual\s*([\d\.,]+)\s*índice"),
            "Viento_Velocidad_kmh": extraer(r"VIENTO.*?elocidad\s*([\d\.,]+)\s*km/h"),
            "Viento_Direccion": m_dir.group(1) if m_dir else "S",
            "Lluvia_Dia_mm": extraer(r"LLUVIA.*?Diaria\s*([\d\.,]+)\s*mm"),
            "ET_Dia_mm": extraer(r"EVAPOTRANSPIRACION.*?Diaria\s*([\d\.,]+)\s*mm")
        }

        # 4. Guardado seguro
        df = pd.DataFrame([datos])
        if not os.path.exists(archivo):
            df.to_csv(archivo, index=False, encoding='utf-8-sig')
        else:
            df.to_csv(archivo, mode='a', header=False, index=False, encoding='utf-8-sig')
            
        print(f"DATOS CAPTURADOS: Temp: {datos['Temperatura_C']} - Hum: {datos['Humedad_pct']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    capturar()
