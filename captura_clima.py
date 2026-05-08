import requests
import pandas as pd
from datetime import datetime
import os
import re

URL_CLIMA = "https://hipodromosanisidro.com/clima/mb3uv.htm"
ARCHIVO_CSV = "registro_clima_san_isidro.csv"

def extraer(etiqueta, texto_completo):
    # Busca la etiqueta y toma el primer número que aparezca después
    try:
        seccion = texto_completo.split(etiqueta)[1]
        match = re.search(r"(\d+[\.,]?\d*)", seccion)
        return match.group(1).replace(',', '.') if match else "0"
    except:
        return "0"

def capturar_todo():
    ahora = datetime.now()
    fecha_str = ahora.strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        res = requests.get(URL_CLIMA, timeout=20)
        res.encoding = 'latin-1'
        t = res.text

        # Extraemos los datos basándonos en las palabras exactas de tu HTML
        registro = {
            "Fecha_Hora": fecha_str,
            "Temperatura_C": extraer("Actual", t),
            "Humedad_pct": extraer("HUMEDAD", t),
            "Punto_Rocio_C": extraer("PUNTO DE ROCIO", t),
            "Presion_hPa": extraer("PRESION BAROMETRICA", t),
            "Radiacion_Solar_Wm2": extraer("RADIACION SOLAR", t),
            "Indice_UV": extraer("RADIACION UV", t),
            "Viento_Velocidad_kmh": extraer("Velocidad", t),
            "Viento_Direccion": "S" if "Sector" not in t else re.search(r"Sector\s+([A-Z]+)", t).group(1),
            "Lluvia_Dia_mm": extraer("LLUVIA", t),
            "ET_Dia_mm": extraer("EVAPOTRANSPIRACION", t)
        }

        df_nuevo = pd.DataFrame([registro])
        
        # Si el archivo no existe, lo crea. Si existe, agrega la fila.
        if not os.path.exists(ARCHIVO_CSV):
            df_nuevo.to_csv(ARCHIVO_CSV, index=False, encoding='utf-8-sig')
        else:
            df_nuevo.to_csv(ARCHIVO_CSV, mode='a', header=False, index=False, encoding='utf-8-sig')
            
        print(f"Datos procesados para: {fecha_str}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    capturar_todo()
