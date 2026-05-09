import requests
import pandas as pd
from datetime import datetime
import os
import re
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def capturar():
    timestamp = int(time.time())
    url = f"https://hipodromosanisidro.com/clima/mb3uv.htm?nocache={timestamp}"
    archivo = "registro_clima_san_isidro.csv"
    carpeta_graficos = "graficos"
    ahora = datetime.now()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }
    
    try:
        # 1. Traer datos limpios
        res = requests.get(url, headers=headers, timeout=30, verify=False)
        res.encoding = 'windows-1252'
        
        # Quitamos etiquetas y normalizamos los espacios
        html_limpio = re.sub(r'<[^>]*>', ' ', res.text).replace('&nbsp;', ' ')
        html_limpio = re.sub(r'\s+', ' ', html_limpio)

        # 2. El Extractor 3D Inteligente
        def extraer(seccion, etiqueta, ocurrencia=1, unidad=None, es_hora=False):
            # Aislamos el bloque para no mezclar Temperatura con Humedad
            secciones = ["TEMPERATURA", "HUMEDAD", "PUNTO DE ROCIO", "SENSACION TERMICA", 
                         "PRESION BAROMETRICA", "VIENTO", "LLUVIA", "EVAPOTRANSPIRACION", 
                         "RADIACION SOLAR", "RADIACION UV"]
            secciones_regex = "|".join(secciones)
            
            bloque = re.search(seccion + r"(.*?)(?=" + secciones_regex + r"|$)", html_limpio, re.IGNORECASE)
            if not bloque:
                return "" if es_hora else "0"
                
            texto_bloque = bloque.group(1)
            
            # Buscamos la fila (ej. "Diaria", "A las")
            idx = texto_bloque.lower().find(etiqueta.lower())
            if idx == -1:
                return "" if es_hora else "0"
                
            sub_texto = texto_bloque[idx:]
            
            # Extraemos Hora o Número según corresponda
            if es_hora:
                matches = re.findall(r"(\d{1,2}:\d{2}[ap])", sub_texto, re.IGNORECASE)
                return matches[ocurrencia-1] if len(matches) >= ocurrencia else ""
            else:
                if unidad:
                    unidad_regex = re.escape(unidad)
                    matches = re.findall(r"([\d\.,]+)\s*" + unidad_regex, sub_texto, re.IGNORECASE)
                else:
                    matches = re.findall(r"([\d\.,]+)", sub_texto)
                    
                if len(matches) >= ocurrencia:
                    return matches[ocurrencia-1].replace(',', '.')
            return "0"

        # 3. MAPEO TOTAL DE CAMPOS
        datos = {
            "Fecha_Hora": ahora.strftime("%Y-%m-%d %H:%M:%S"),
            
            # --- TEMPERATURA ---
            "Temp_Actual_C": extraer("TEMPERATURA", "Actual", 1, "°C"),
            "Temp_Min_Diaria_C": extraer("TEMPERATURA", "Diaria", 1, "°C"),
            "Temp_Max_Diaria_C": extraer("TEMPERATURA", "Diaria", 2, "°C"),
            "Temp_Hora_Min": extraer("TEMPERATURA", "A las", 1, es_hora=True),
            "Temp_Hora_Max": extraer("TEMPERATURA", "A las", 2, es_hora=True),
            "Temp_Min_Mensual_C": extraer("TEMPERATURA", "Mensual", 1, "°C"),
            "Temp_Max_Mensual_C": extraer("TEMPERATURA", "Mensual", 2, "°C"),
            "Temp_Min_Anual_C": extraer("TEMPERATURA", "Anual", 1, "°C"),
            "Temp_Max_Anual_C": extraer("TEMPERATURA", "Anual", 2, "°C"),
            
            # --- HUMEDAD ---
            "Hum_Actual_pct": extraer("HUMEDAD", "Actual", 1, "%"),
            "Hum_Min_Diaria_pct": extraer("HUMEDAD", "Diaria", 1, "%"),
            "Hum_Max_Diaria_pct": extraer("HUMEDAD", "Diaria", 2, "%"),
            "Hum_Hora_Min": extraer("HUMEDAD", "A las", 1, es_hora=True),
            "Hum_Hora_Max": extraer("HUMEDAD", "A las", 2, es_hora=True),
            "Hum_Min_Mensual_pct": extraer("HUMEDAD", "Mensual", 1, "%"),
            "Hum_Max_Mensual_pct": extraer("HUMEDAD", "Mensual", 2, "%"),
            "Hum_Min_Anual_pct": extraer("HUMEDAD", "Anual", 1, "%"),
            "Hum_Max_Anual_pct": extraer("HUMEDAD", "Anual", 2, "%"),
            
            # --- PUNTO DE ROCIO Y SENSACION ---
            "Punto_Rocio_Actual_C": extraer("PUNTO DE ROCIO", "Actual", 1, "°C"),
            "Sensacion_Viento_C": extraer("SENSACION TERMICA", "Viento", 1, "°C"),
            "Sensacion_Humedad_C": extraer("SENSACION TERMICA", "Humedad", 1, "°C"),
            "Presion_Actual_hPa": extraer("PRESION BAROMETRICA", "Actual", 1, "hPa"),
            
            # --- VIENTO ---
            "Viento_Vel_Actual_kmh": extraer("VIENTO", "elocidad", 1, "km/h"),
            "Viento_Direccion": "S", # Se asigna abajo
            "Viento_Max_Diaria_kmh": extraer("VIENTO", "Diaria", 1, "km/h"),
            "Viento_Hora_Max": extraer("VIENTO", "A las", 1, es_hora=True),
            "Viento_Max_Mensual_kmh": extraer("VIENTO", "Mensual", 1, "km/h"),
            "Viento_Max_Anual_kmh": extraer("VIENTO", "Anual", 1, "km/h"),
            
            # --- LLUVIA Y EVAPOTRANSPIRACION ---
            "Lluvia_Diaria_mm": extraer("LLUVIA", "Diaria", 1, "mm"),
            "Lluvia_Intensidad_mmh": extraer("LLUVIA", "Intensidad", 1, "mm/h"),
            "Lluvia_Mensual_mm": extraer("LLUVIA", "Mensual", 1, "mm"),
            "Lluvia_Anual_mm": extraer("LLUVIA", "Anual", 1, "mm"),
            "ET_Diaria_mm": extraer("EVAPOTRANSPIRACION", "Diaria", 1, "mm"),
            "ET_Mensual_mm": extraer("EVAPOTRANSPIRACION", "Mensual", 1, "mm"),
            "ET_Anual_mm": extraer("EVAPOTRANSPIRACION", "Anual", 1, "mm"),
            
            # --- RADIACION ---
            "Rad_Solar_Actual_Wm2": extraer("RADIACION SOLAR", "Actual", 1, "W/m"),
            "UV_Actual_Indice": extraer("RADIACION UV", "Actual", 1, "índice"),
            "UV_Max_Diaria": extraer("RADIACION UV", "Diaria", 1, "índice"),
            "UV_Hora_Max": extraer("RADIACION UV", "A las", 1, es_hora=True),
            "UV_Max_Mensual": extraer("RADIACION UV", "Mensual", 1, "índice"),
            "UV_Max_Anual": extraer("RADIACION UV", "Anual", 1, "índice")
        }

        # Extracción especial para la dirección del viento
        m_dir = re.search(r"Sector\s*([A-Z]+)", html_limpio)
        if m_dir:
            datos["Viento_Direccion"] = m_dir.group(1)

        # 4. GRABADO EN CSV
        df_nuevo = pd.DataFrame([datos])
        
        if os.path.exists(archivo) and os.path.getsize(archivo) > 0:
            try:
                df_existente = pd.read_csv(archivo)
                df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
                df_final.to_csv(archivo, index=False, encoding='utf-8-sig')
            except:
                df_nuevo.to_csv(archivo, index=False, encoding='utf-8-sig')
        else:
            # Si el archivo no existe o estaba vacío, lo crea con los títulos
            df_nuevo.to_csv(archivo, index=False, encoding='utf-8-sig')
                
        print("¡CAPTURA TOTAL EXITOSA!")

        # 5. Capturar los Gráficos de la página (Opcional, podés borrarlo si no lo usás)
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
