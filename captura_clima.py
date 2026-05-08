import requests
import pandas as pd
from datetime import datetime
import os
import re

def capturar_todo():
    url = "https://hipodromosanisidro.com/clima/mb3uv.htm"
    archivo = "registro_clima_san_isidro.csv"
    
    try:
        res = requests.get(url, timeout=30)
        res.encoding = 'latin-1'
        t = res.text

        # Busqueda ultra-simple por palabras clave
        def f(label):
            try:
                # Busca el numero mas cercano despues de la palabra clave
                return re.search(label + r".*?(\d+[\.,]?\d*)", t, re.S).group(1).replace(',', '.')
            except:
                return "0"

        nuevo_dato = {
            "Fecha_Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Temperatura_C": f("Actual"),
            "Humedad_pct": f("HUMEDAD"),
            "Punto_Rocio_C": f("PUNTO DE ROCIO"),
            "Presion_hPa": f("BAROMETRICA"),
            "Radiacion_Solar_Wm2": f("RADIACION SOLAR"),
            "Indice_UV": f("RADIACION UV"),
            "Viento_Velocidad_kmh": f("Velocidad"),
            "Viento_Direccion": "S" if "Sector" not in t else re.search(r"Sector\s+([A-Z]+)", t).group(1),
            "Lluvia_Dia_mm": f("LLUVIA"),
            "ET_Dia_mm": f("EVAPOTRANSPIRACION")
        }

        df = pd.DataFrame([nuevo_dato])
        # Escribe al final del archivo (append)
        df.to_csv(archivo, mode='a', header=not os.path.exists(archivo), index=False, encoding='utf-8-sig')
        print("Datos guardados en el archivo local del robot.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    capturar_todo()
