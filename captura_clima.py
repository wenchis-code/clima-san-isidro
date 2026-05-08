import requests
import pandas as pd
from datetime import datetime
import os
import re

URL_CLIMA = "https://hipodromosanisidro.com/clima/mb3uv.htm"
ARCHIVO_CSV = "registro_clima_san_isidro.csv"

def extraer(patron, texto):
    # Busca un número antes o después de una palabra clave
    regex = re.compile(patron, re.IGNORECASE | re.DOTALL)
    match = regex.search(texto)
    if match:
        valor = match.group(1).replace(',', '.')
        return re.sub(r'[^0-9.]', '', valor)
    return "0"

def capturar_todo():
    ahora = datetime.now()
    fecha_str = ahora.strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        res = requests.get(URL_CLIMA, timeout=20)
        res.encoding = 'latin-1'
        t = res.text

        # Diccionario con los datos limpios
        registro = {
            "Fecha_Hora": fecha_str,
            "Temperatura_C": extraer(r"Actual.*?(\d+[\.,]?\d*)\s*°C", t),
            "Humedad_pct": extraer(r"HUMEDAD.*?Actual.*?(\d+)\s*%", t),
            "Punto_Rocio_C": extraer(r"PUNTO DE ROCIO.*?Actual.*?(\d+[\.,]?\d*)\s*°C", t),
            "Presion_hPa": extraer(r"BAROMETRICA.*?Actual.*?(\d+[\.,]?\d*)\s*hPa", t),
            "Radiacion_Solar_Wm2": extraer(r"SOLAR.*?Actual.*?(\d+)\s*W/m²", t),
            "Indice_UV": extraer(r"UV.*?Actual.*?(\d+[\.,]?\d*)\s*índice", t),
            "Viento_Velocidad_kmh": extraer(r"Velocidad.*?(\d+[\.,]?\d*)\s*km/h", t),
            "Viento_Direccion": "S" if "Sector" not in t else re.search(r"Sector\s+([A-Z]+)", t).group(1),
            "Lluvia_Dia_mm": extraer(r"LLUVIA.*?Diaria.*?(\d+[\.,]?\d*)\s*mm", t),
            "ET_Dia_mm": extraer(r"EVAPOTRANSPIRACION.*?Diaria.*?(\d+[\.,]?\d*)\s*mm", t)
        }

        # FORZAR ESCRITURA: Creamos el DataFrame y lo guardamos
        df_nuevo = pd.DataFrame([registro])
        
        if not os.path.exists(ARCHIVO_CSV):
            df_nuevo.to_csv(ARCHIVO_CSV, index=False, encoding='utf-8-sig')
        else:
            # Leemos el existente, pegamos el nuevo y guardamos todo de nuevo
            df_existente = pd.read_csv(ARCHIVO_CSV)
            df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
            df_final.to_csv(ARCHIVO_CSV, index=False, encoding='utf-8-sig')
            
        print(f"Fila grabada exitosamente para {fecha_str}")

    except Exception as e:
        print(f"Error al grabar: {e}")

if __name__ == "__main__":
    capturar_todo()
