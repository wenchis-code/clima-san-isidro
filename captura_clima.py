import requests
import pandas as pd
from datetime import datetime
import os
import re
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def capturar():
    archivo = "registro_clima_san_isidro.csv"
    carpeta_graficos = "graficos"
    ahora = datetime.now()
    fecha_captura = ahora.strftime("%Y-%m-%d %H:%M:%S")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cache-Control': 'no-cache, no-store, must-revalidate'
    }
    
    html_limpio = ""
    exito_conexion = False

    for intento in range(3):
        try:
            timestamp = int(time.time())
            url = f"https://hipodromosanisidro.com/clima/mb3uv.htm?nocache={timestamp}"
            res = requests.get(url, headers=headers, timeout=20, verify=False)
            res.encoding = 'windows-1252'
            html_limpio = re.sub(r'<[^>]*>', ' ', res.text).replace('&nbsp;', ' ')
            html_limpio = re.sub(r'\s+', ' ', html_limpio)
            exito_conexion = True
            break
        except:
            time.sleep(5)

    def extraer(seccion, etiqueta, ocurrencia=1, unidad=None, es_hora=False):
        if not exito_conexion: return "ERROR"
        secciones = ["TEMPERATURA", "HUMEDAD", "PUNTO DE ROCIO", "SENSACION TERMICA", 
                     "PRESION BAROMETRICA", "VIENTO", "LLUVIA", "EVAPOTRANSPIRACION", 
                     "RADIACION SOLAR", "RADIACION UV"]
        secciones_regex = "|".join(secciones)
        bloque = re.search(seccion + r"(.*?)(?=" + secciones_regex + r"|$)", html_limpio, re.IGNORECASE)
        if not bloque: return "" if es_hora else "0"
        texto_bloque = bloque.group(1)
        idx = texto_bloque.lower().find(etiqueta.lower())
        if idx == -1: return "" if es_hora else "0"
        sub_texto = texto_bloque[idx:]
        if es_hora:
            matches = re.findall(r"(\d{1,2}:\d{2}[ap])", sub_texto, re.IGNORECASE)
            return matches[ocurrencia-1] if len(matches) >= ocurrencia else ""
        else:
            if unidad:
                matches = re.findall(r"([\d\.,]+)\s*" + re.escape(unidad), sub_texto, re.IGNORECASE)
            else:
                matches = re.findall(r"([\d\.,]+)", sub_texto)
            return matches[ocurrencia-1].replace(',', '.') if len(matches) >= ocurrencia else "0"

    # --- EXTRACCIÓN DE ENCABEZADO (Fecha/Hora de la Web) ---
    web_fecha = "0"
    web_hora = "0"
    if exito_conexion:
        m_f = re.search(r"FECHA:\s*([\d/]+)", html_limpio, re.I)
        m_h = re.search(r"HORA:\s*([\d:ap\s]+)", html_limpio, re.I)
        web_fecha = m_f.group(1).strip() if m_f else "0"
        web_hora = m_h.group(1).strip() if m_h else "0"

    # --- MAPEO TOTAL ---
    datos = {
        "Captura_Sistema": fecha_captura,
        "Web_Fecha_Origen": web_fecha,
        "Web_Hora_Origen": web_hora,
        
        # TEMPERATURA
        "Temp_Actual_C": extraer("TEMPERATURA", "Actual", 1, "°C"),
        "Temp_Min_Diaria_C": extraer("TEMPERATURA", "Diaria", 1, "°C"),
        "Temp_Max_Diaria_C": extraer("TEMPERATURA", "Diaria", 2, "°C"),
        "Temp_Hora_Min": extraer("TEMPERATURA", "A las", 1, es_hora=True),
        "Temp_Hora_Max": extraer("TEMPERATURA", "A las", 2, es_hora=True),
        "Temp_Min_Mensual_C": extraer("TEMPERATURA", "Mensual", 1, "°C"),
        "Temp_Max_Mensual_C": extraer("TEMPERATURA", "Mensual", 2, "°C"),
        
        # HUMEDAD
        "Hum_Actual_pct": extraer("HUMEDAD", "Actual", 1, "%"),
        "Hum_Min_Diaria_pct": extraer("HUMEDAD", "Diaria", 1, "%"),
        "Hum_Max_Diaria_pct": extraer("HUMEDAD", "Diaria", 2, "%"),
        "Hum_Hora_Min": extraer("HUMEDAD", "A las", 1, es_hora=True),
        "Hum_Hora_Max": extraer("HUMEDAD", "A las", 2, es_hora=True),
        
        # OTROS
        "Punto_Rocio_C": extraer("PUNTO DE ROCIO", "Actual", 1, "°C"),
        "Presion_hPa": extraer("PRESION BAROMETRICA", "Actual", 1, "hPa"),
        
        # VIENTO
        "Viento_Vel_kmh": extraer("VIENTO", "elocidad", 1, "km/h"),
        "Viento_Dir": (re.search(r"Sector\s*([A-Z]+)", html_limpio).group(1) if exito_conexion and re.search(r"Sector\s*([A-Z]+)", html_limpio) else "S"),
        "Viento_Max_kmh": extraer("VIENTO", "Diaria", 1, "km/h"),
        "Viento_Hora_Max": extraer("VIENTO", "A las", 1, es_hora=True),
        
        # LLUVIA
        "Lluvia_Dia_mm": extraer("LLUVIA", "Diaria", 1, "mm"),
        "Lluvia_Mes_mm": extraer("LLUVIA", "Mensual", 1, "mm"),
        "ET_Dia_mm": extraer("EVAPOTRANSPIRACION", "Diaria", 1, "mm"),
        
        # RADIACION
        "Rad_Solar_Wm2": extraer("RADIACION SOLAR", "Actual", 1, "W/m"),
        "UV_Indice": extraer("RADIACION UV", "Actual", 1, "índice"),
        "UV_Max_Diaria": extraer("RADIACION UV", "Diaria", 1, "índice"),
        "UV_Hora_Max": extraer("RADIACION UV", "A las", 1, es_hora=True)
    }

    # --- GUARDADO ---
    df_nuevo = pd.DataFrame([datos])
    if os.path.exists(archivo) and os.path.getsize(archivo) > 0:
        try:
            df_existente = pd.read_csv(archivo)
            pd.concat([df_existente, df_nuevo], ignore_index=True).to_csv(archivo, index=False, encoding='utf-8-sig')
        except:
            df_nuevo.to_csv(archivo, index=False, encoding='utf-8-sig')
    else:
        df_nuevo.to_csv(archivo, index=False, encoding='utf-8-sig')
    
    print(f"DATOS GRABADOS. Web Date: {web_fecha} {web_hora}")

if __name__ == "__main__":
    capturar()
