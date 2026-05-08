import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import re

URL_CLIMA = "https://hipodromosanisidro.com/clima/mb3uv.htm"
BASE_URL_IMG = "https://hipodromosanisidro.com/clima/"
ARCHIVO_CSV = "registro_clima_san_isidro.csv"
CARPETA_GRAFICOS = "graficos"

def limpiar_valor(texto):
    # Esta función quita letras y símbolos, dejando solo el número y el punto
    return re.sub(r'[^0-9.]', '', texto.replace(',', '.'))

def capturar_todo():
    ahora = datetime.now()
    fecha_hora_str = ahora.strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        res = requests.get(URL_CLIMA, timeout=20)
        res.encoding = 'latin-1' # Para que no aparezcan los símbolos raros
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Buscamos todas las celdas de la tabla
        celdas = soup.find_all('td')
        textos = [c.get_text(strip=True) for c in celdas]

        # Mapeo de posiciones exactas según la estructura de la Davis Vantage Pro2
        registro = {
            "Fecha_Hora": fecha_hora_str,
            "Temperatura_C": limpiar_valor(textos[6]),
            "Humedad_pct": limpiar_valor(textos[10]),
            "Punto_Rocio_C": limpiar_valor(textos[12]),
            "Presion_hPa": limpiar_valor(textos[22]),
            "Radiacion_Solar_Wm2": limpiar_valor(textos[30]),
            "Indice_UV": limpiar_valor(textos[32]),
            "Viento_Velocidad_kmh": limpiar_valor(textos[14]),
            "Viento_Direccion": textos[16].replace('Â', '').strip(), # La dirección es texto (ej: NNE)
            "Lluvia_Dia_mm": limpiar_valor(textos[26]),
            "ET_Dia_mm": limpiar_valor(textos[34])
        }

        df = pd.DataFrame([registro])
        header = not os.path.exists(ARCHIVO_CSV)
        df.to_csv(ARCHIVO_CSV, mode='a', index=False, header=header, encoding='utf-8-sig')
        print(f"Captura limpia realizada: {registro['Temperatura_C']}°C")

        # Captura de gráficos (Solo a las 23hs)
        if ahora.hour == 23:
            if not os.path.exists(CARPETA_GRAFICOS): os.makedirs(CARPETA_GRAFICOS)
            fecha_img = ahora.strftime("%Y%m%d")
            for g in ["temp.gif", "hum.gif", "baro.gif", "wind.gif", "rain.gif", "uv.gif", "solar.gif"]:
                try:
                    img_res = requests.get(BASE_URL_IMG + g, timeout=15)
                    with open(f"{CARPETA_GRAFICOS}/{fecha_img}_{g}", 'wb') as f:
                        f.write(img_res.content)
                except: continue

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    capturar_todo()
