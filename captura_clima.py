import requests
import pandas as pd
from datetime import datetime
import os
import re
import urllib3
import time

# Evita las alertas de conexión
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def capturar():
    # EL TRUCO ROMPE-CACHÉ: Agregamos la hora exacta a la URL para forzar datos frescos
    timestamp = int(time.time())
    url = f"https://hipodromosanisidro.com/clima/mb3uv.htm?nocache={timestamp}"
    archivo = "registro_clima_san_isidro.csv"
    carpeta_graficos = "graficos"
    ahora = datetime.now()

    # Disfraz con órdenes estrictas de NO usar memoria caché
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }
    
    try:
        # 1. Obtener los datos frescos
        res = requests.get(url, headers=headers, timeout=30, verify=False)
        res.encoding = 'windows-1252'
        html_limpio = re.sub(r'<[^>]*>', ' ', res.text).replace('&nbsp;', ' ')

        # 2. Función extractora
        def ext(patron):
            m = re.search(patron, html_limpio, re.IGNORECASE | re.S)
            if m:
                return re.sub(r'[^0-9.]', '', m.group(1).replace(',', '.'))
            return "0"

        # 3. Capturar cada uno de los 11 datos
        datos = {
            "Fecha_Hora": ahora.strftime("%Y-%m-%d %H:%M:%S"),
            "Temperatura_C": ext(r"TEMPERATURA.*?Actual\s*([\d\.,]+)\s*°C"),
            "Humedad_pct": ext(r"HUMEDAD.*?Actual\s*([\d\.,]+)\s*%"),
            "Punto_Rocio_C": ext(r"PUNTO\s+DE\s+ROCIO.*?Actual\s*([\d\.,]+)\s*°C"),
            "Presion_hPa": ext(r"PRESION\s+BAROMETRICA.*?Actual\s*([\d\.,]+)\s*hPa"),
            "Radiacion_Solar_Wm2": ext(r"RADIACION\s+SOLAR.*?Actual\s*([\d\.,]+)\s*W/m"),
            "Indice_UV": ext(r"RADIACION\s+UV.*?Actual\s*([\d\.,]+)\s*índice"),
            "Viento_Velocidad_kmh": ext(r"VIENTO.*?elocidad\s*([\d\.,]+)\s*km/h"),
            "Viento_Direccion": "S", 
            "Lluvia_Dia_mm": ext(r"LLUVIA.*?Diaria\s*([\d\.,]+)\s*mm"),
            "ET_Dia_mm": ext(r"EVAPOTRANSPIRACION.*?Diaria\s*([\d\.,]+)\s*mm")
        }

        m_dir = re.search(r"Sector\s*([A-Z]+)", html_limpio)
        if m_dir:
            datos["Viento_Direccion"] = m_dir.group(1)

        # 4. GRABADO A PRUEBA DE BALAS CON PANDAS
        df_nuevo = pd.DataFrame([datos])
        
        if os.path.exists(archivo) and os.path.getsize(archivo) > 0:
            try:
                df_existente = pd.read_csv(archivo)
                df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
                df_final.to_csv(archivo, index=False, encoding='utf-8-sig')
            except:
                df_nuevo.to_csv(archivo, index=False, encoding='utf-8-sig')
        else:
            df_nuevo.to_csv(archivo, index=False, encoding='utf-8-sig')
                
        print(f"DATOS FRESCOS GRABADOS: {datos}")

        # 5. Capturar los Gráficos
        if not os.path.exists(carpeta_graficos):
            os.makedirs(carpeta_graficos)
            
        graficos = ["OutsideTempHistory.gif", "OutsideHumidityHistory.gif", "BarometerHistory.gif", "WindSpeedHistory.gif", "RainHistory.gif"]
        base_img_url = "https://hipodromosanisidro.com/clima/"
        
        for g in graficos:
            try:
                img_data = requests.get(base_img_url + g + f"?nocache={timestamp}", headers=headers, verify=False, timeout=10).content
                ruta_img = f"{carpeta_graficos}/{ahora.strftime('%Y%m%d')}_{g}"
                with open(ruta_img, 'wb') as f:
                    f.write(img_data)
            except:
                pass

    except Exception as e:
        print(f"Error general: {e}")

if __name__ == "__main__":
    capturar()
