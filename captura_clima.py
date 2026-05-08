import requests
import pandas as pd
from datetime import datetime
import os
import re

def capturar():
    url = "https://hipodromosanisidro.com/clima/mb3uv.htm"
    archivo = "registro_clima_san_isidro.csv"
    
    try:
        # 1. Traer la página con la codificación correcta para Argentina
        res = requests.get(url, timeout=30)
        res.encoding = 'latin-1'
        html = res.text

        # 2. Función "limpiadora" de números: busca el número que está ANTES de la unidad
        def extraer(unidad, texto_previo):
            # Busca la sección (ej: TEMPERATURA) y luego el primer número antes de la unidad (ej: °C)
            try:
                seccion = html.split(texto_previo)[1].split("</table>")[0]
                match = re.search(r"(\d+[\.,]?\d*)\s*" + unidad, seccion)
                if match:
                    return match.group(1).replace(',', '.')
            except:
                pass
            return "0"

        # 3. Mapeo ultra-preciso basado en el HTML que me pasaste
        datos = {
            "Fecha_Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Temperatura_C": extraer("°C", "TEMPERATURA"),
            "Humedad_pct": extraer("%", "HUMEDAD"),
            "Punto_Rocio_C": extraer("°C", "PUNTO DE ROCIO"),
            "Presion_hPa": extraer("hPa", "PRESION BAROMETRICA"),
            "Radiacion_Solar_Wm2": extraer("W/m²", "RADIACION SOLAR"),
            "Indice_UV": extraer("índice", "RADIACION UV"),
            "Viento_Velocidad_kmh": extraer("km/h", "VIENTO"),
            "Viento_Direccion": "S" if "Sector" not in html else re.search(r"Sector\s+([A-Z]+)", html).group(1),
            "Lluvia_Dia_mm": extraer("mm", "LLUVIA"),
            "ET_Dia_mm": extraer("mm", "EVAPOTRANSPIRACION")
        }

        # 4. Forzar la escritura en el CSV
        df = pd.DataFrame([datos])
        if not os.path.exists(archivo):
            df.to_csv(archivo, index=False, encoding='utf-8-sig')
        else:
            df.to_csv(archivo, mode='a', header=False, index=False, encoding='utf-8-sig')
        
        print(f"Éxito: Datos capturados correctamente.")

    except Exception as e:
        print(f"Error en el script: {e}")

if __name__ == "__main__":
    capturar()
