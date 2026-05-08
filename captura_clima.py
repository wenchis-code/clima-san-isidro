import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os

# Configuración de URLs y Archivos
URL_CLIMA = "https://hipodromosanisidro.com/clima/mb3uv.htm"
BASE_URL_IMG = "https://hipodromosanisidro.com/clima/"
ARCHIVO_CSV = "registro_clima_san_isidro.csv"
CARPETA_GRAFICOS = "graficos"

def capturar_todo():
    ahora = datetime.now()
    fecha_hora_str = ahora.strftime("%Y-%m-%d %H:%M:%S")
    print(f"Iniciando captura: {fecha_hora_str}")

    try:
        # 1. CAPTURA DE DATOS NUMÉRICOS
        res = requests.get(URL_CLIMA, timeout=20)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        datos = [td.get_text(strip=True) for td in soup.find_all('td')]

        registro = {
            "Fecha_Hora": fecha_hora_str,
            "Temperatura_C": datos[6],
            "Humedad_pct": datos[10],
            "Punto_Rocio_C": datos[12],
            "Presion_hPa": datos[22],
            "Radiacion_Solar_Wm2": datos[30],
            "Indice_UV": datos[32],
            "Viento_Velocidad_kmh": datos[14],
            "Viento_Direccion": datos[16],
            "Lluvia_Dia_mm": datos[26],
            "ET_Dia_mm": datos[34]
        }

        # Guardar en CSV
        df = pd.DataFrame([registro])
        header = not os.path.exists(ARCHIVO_CSV)
        df.to_csv(ARCHIVO_CSV, mode='a', index=False, header=header, encoding='utf-8-sig')
        print("Valores numéricos guardados.")

        # 2. CAPTURA DE GRÁFICOS (Solo a las 23hs para el cierre diario)
        if ahora.hour == 23:
            if not os.path.exists(CARPETA_GRAFICOS):
                os.makedirs(CARPETA_GRAFICOS)
            
            fecha_img = ahora.strftime("%Y%m%d")
            graficos = ["temp.gif", "hum.gif", "baro.gif", "wind.gif", "rain.gif", "uv.gif", "solar.gif"]
            
            for g in graficos:
                try:
                    img_res = requests.get(BASE_URL_IMG + g, timeout=15)
                    if img_res.status_code == 200:
                        with open(f"{CARPETA_GRAFICOS}/{fecha_img}_{g}", 'wb') as f:
                            f.write(img_res.content)
                except:
                    continue
            print("Gráficos de cierre diario guardados.")

    except Exception as e:
        print(f"Error en la captura: {e}")

if __name__ == "__main__":
    capturar_todo()
