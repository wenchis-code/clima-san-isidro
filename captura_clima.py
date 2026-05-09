import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def capturar():
    url = "https://hipodromosanisidro.com/clima/mb3uv.htm"
    base_img_url = "https://hipodromosanisidro.com/clima/"
    archivo_csv = "registro_clima_san_isidro.csv"
    carpeta_graficos = "graficos"
    ahora = datetime.now()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        # 1. Traer la página
        res = requests.get(url, headers=headers, timeout=30, verify=False)
        res.encoding = 'windows-1252'
        
        # USAMOS BEAUTIFULSOUP: El lector de planos
        soup = BeautifulSoup(res.text, 'html.parser')

        # Función inteligente para buscar un valor en una tabla
        def buscar_valor(etiqueta_titulo):
            # Busca la celda que contiene el título exacto (ej. "TEMPERATURA")
            celda_titulo = soup.find(string=lambda text: text and etiqueta_titulo in text)
            if celda_titulo:
                # Sube a la tabla principal de esa sección y extrae todo su texto
                tabla = celda_titulo.find_parent('table')
                if tabla:
                    texto_tabla = tabla.get_text(separator=" ", strip=True)
                    return texto_tabla
            return ""

        # Obtenemos los textos limpios por bloques (ignorando el desorden del HTML)
        bloque_temp = buscar_valor("TEMPERATURA")
        bloque_hum = buscar_valor("HUMEDAD")
        bloque_pres = buscar_valor("PRESION BAROMETRICA")
        bloque_viento = buscar_valor("VIENTO")
        bloque_lluvia = buscar_valor("LLUVIA")

        # Función auxiliar para limpiar números
        def extraer_numero(texto, separador_previo, unidad):
            try:
                parte = texto.split(separador_previo)[1]
                num = parte.split(unidad)[0].strip().replace(',', '.')
                return ''.join(c for c in num if c.isdigit() or c == '.')
            except:
                return "0"

        # Extraemos con precisión milimétrica de cada bloque aislado
        datos = {
            "Fecha_Hora": ahora.strftime("%Y-%m-%d %H:%M:%S"),
            "Temperatura_C": extraer_numero(bloque_temp, "Actual", "°C"),
            "Humedad_pct": extraer_numero(bloque_hum, "Actual", "%"),
            "Presion_hPa": extraer_numero(bloque_pres, "Actual", "hPa"),
            "Viento_Velocidad_kmh": extraer_numero(bloque_viento, "elocidad", "km/h"),
            "Lluvia_Dia_mm": extraer_numero(bloque_lluvia, "Diaria", "mm")
        }

        # 2. GUARDAR DATOS EN CSV
        df = pd.DataFrame([datos])
        if not os.path.exists(archivo_csv):
            df.to_csv(archivo_csv, index=False, encoding='utf-8-sig')
        else:
            df.to_csv(archivo_csv, mode='a', header=False, index=False, encoding='utf-8-sig')
            
        print(f"Datos grabados: {datos}")

        # 3. DESCARGAR GRÁFICOS (Solo una vez al día a las 23hs para tener el resumen del día, o podés sacarle el 'if' para que baje siempre)
        if not os.path.exists(carpeta_graficos):
            os.makedirs(carpeta_graficos)
            
        graficos = [
            "OutsideTempHistory.gif", 
            "OutsideHumidityHistory.gif", 
            "BarometerHistory.gif", 
            "WindSpeedHistory.gif", 
            "RainHistory.gif"
        ]
        
        for grafico in graficos:
            try:
                img_data = requests.get(base_img_url + grafico, headers=headers, verify=False, timeout=10).content
                # Guarda la imagen con la fecha de hoy
                ruta_img = f"{carpeta_graficos}/{ahora.strftime('%Y%m%d')}_{grafico}"
                with open(ruta_img, 'wb') as f:
                    f.write(img_data)
            except Exception as e:
                print(f"No se pudo descargar {grafico}: {e}")

    except Exception as e:
        print(f"Error general: {e}")

if __name__ == "__main__":
    capturar()
