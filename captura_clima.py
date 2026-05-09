import requests
import pandas as pd
from datetime import datetime
import os
import re
import urllib3

# Ocultar advertencias de seguridad de la página
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def capturar():
    url = "https://hipodromosanisidro.com/clima/mb3uv.htm"
    archivo = "registro_clima_san_isidro.csv"
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # 1. DISFRAZ: Simulamos ser un humano usando Google Chrome en Windows
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # verify=False permite entrar aunque el certificado de la web esté vencido
        res = requests.get(url, headers=headers, timeout=30, verify=False)
        res.encoding = 'windows-1252'
        html = res.text

        html_limpio = re.sub(r'<[^>]*>', ' ', html).replace('&nbsp;', ' ')

        def extraer(patron):
            match = re.search(patron, html_limpio, re.IGNORECASE | re.DOTALL)
            if match:
                val = match.group(1).replace(',', '.')
                return re.sub(r'[^0-9.]', '', val)
            return "0"

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

        # Guardado normal si todo sale bien
        df = pd.DataFrame([datos])
        if not os.path.exists(archivo):
            df.to_csv(archivo, index=False, encoding='utf-8-sig')
        else:
            df.to_csv(archivo, mode='a', header=False, index=False, encoding='utf-8-sig')
            
        print(f"DATOS CAPTURADOS: Temp: {datos['Temperatura_C']} - Hum: {datos['Humedad_pct']}")

    except Exception as e:
        print(f"Error de conexión o bloqueo: {e}")
        # TRAMPA: Si falla la conexión, escribe ERROR en el CSV para forzar el guardado
        datos_error = {
            "Fecha_Hora": ahora,
            "Temperatura_C": "ERROR",
            "Humedad_pct": "ERROR",
            "Punto_Rocio_C": "0",
            "Presion_hPa": "0",
            "Radiacion_Solar_Wm2": "0",
            "Indice_UV": "0",
            "Viento_Velocidad_kmh": "0",
            "Viento_Direccion": "0",
            "Lluvia_Dia_mm": "0",
            "ET_Dia_mm": "0"
        }
        df_err = pd.DataFrame([datos_error])
        if not os.path.exists(archivo):
            df_err.to_csv(archivo, index=False, encoding='utf-8-sig')
        else:
            df_err.to_csv(archivo, mode='a', header=False, index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    capturar()
