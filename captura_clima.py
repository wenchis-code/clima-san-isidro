import requests
import pandas as pd
from datetime import datetime
import os
import re

def capturar():
    url = "https://hipodromosanisidro.com/clima/mb3uv.htm"
    archivo = "registro_clima_san_isidro.csv"
    
    try:
        # 1. Traer la página
        res = requests.get(url, timeout=30)
        res.encoding = 'latin-1'
        html = res.text

        # 2. Función "limpiadora" de números
        def extraer(patron):
            match = re.search(patron, html, re.DOTALL | re.IGNORECASE)
            if match:
                # Limpia el número de comas y símbolos
                num = match.group(1).replace(',', '.')
                return re.sub(r'[^0-9.]', '', num)
            return "0"

        # 3. Mapeo por unidades (esto no falla aunque cambien la tabla)
        datos = {
            "Fecha_Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Temperatura_C": extraer(r"TEMPERATURA.*?Actual.*?(\d+[\.,]?\d*)\s*°C"),
            "Humedad_pct": extraer(r"HUMEDAD.*?Actual.*?(\d+)\s*%"),
            "Punto_Rocio_C": extraer(r"PUNTO DE ROCIO.*?Actual.*?(\d+[\.,]?\d*)\s*°C"),
            "Presion_hPa": extraer(r"PRESION BAROMETRICA.*?Actual.*?(\d+[\.,]?\d*)\s*hPa"),
            "Radiacion_Solar_Wm2": extraer(r"RADIACION SOLAR.*?Actual.*?(\d+)\s*W/m²"),
            "Indice_UV": extraer(r"RADIACION UV.*?Actual.*?(\d+[\.,]?\d*)\s*índice"),
            "Viento_Velocidad_kmh": extraer(r"VIENTO.*?Velocidad.*?(\d+[\.,]?\d*)\s*km/h"),
            "Viento_Direccion": "S" if "Sector" not in html else re.search(r"Sector\s+([A-Z]+)", html).group(1),
            "Lluvia_Dia_mm": extraer(r"LLUVIA.*?Diaria.*?(\d+[\.,]?\d*)\s*mm"),
            "ET_Dia_mm": extraer(r"EVAPOTRANSPIRACION.*?Diaria.*?(\d+[\.,]?\d*)\s*mm")
        }

        # 4. Forzar la escritura
        df = pd.DataFrame([datos])
        if not os.path.exists(archivo):
            df.to_csv(archivo, index=False, encoding='utf-8-sig')
        else:
            df.to_csv(archivo, mode='a', header=False, index=False, encoding='utf-8-sig')
        
        print(f"Éxito: Se capturó Temp {datos['Temperatura_C']}°C")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    capturar()
