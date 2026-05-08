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

def extraer_numero(texto):
    # Extrae el primer número (entero o decimal) que encuentre en un texto
    match = re.search(r"[-+]?\d*\.\d+|\d+", texto.replace(',', '.'))
    return match.group() if match else ""

def capturar_todo():
    ahora = datetime.now()
    fecha_hora_str = ahora.strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        res = requests.get(URL_CLIMA, timeout=20)
        res.encoding = 'latin-1'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Convertimos toda la página en una lista de palabras para buscar fácil
        celdas = [c.get_text(" ", strip=True) for c in soup.find_all(['td', 'font'])]
        texto_completo = " ".join(celdas)

        # Buscamos cada dato por su "nombre" en la página
        def buscar(etiqueta, despues_de=0):
            for i, t in enumerate(celdas):
                if etiqueta in t.upper():
                    # El dato suele estar en la celda siguiente o en la misma
                    return celdas[i+1] if i+1 < len(celdas) else ""
            return ""

        registro = {
            "Fecha_Hora": fecha_hora_str,
            "Temperatura_C": extraer_numero(buscar("ACTUAL")), # Busca donde dice Actual [Temp]
            "Humedad_pct": extraer_numero(buscar("HUMEDAD")),
            "Punto_Rocio_C": extraer_numero(buscar("PUNTO DE ROCIO")),
            "Presion_hPa": extraer_numero(buscar("BAROMETRO")),
            "Radiacion_Solar_Wm2": extraer_numero(buscar("RADIACION SOLAR")),
            "Indice_UV": extraer_numero(buscar("INDICE UV")),
            "Viento_Velocidad_kmh": extraer_numero(buscar("VIENTO")),
            "Viento_Direccion": buscar("VIENTO").split()[-1] if buscar("VIENTO") else "", 
            "Lluvia_Dia_mm": extraer_numero(buscar("LLUVIA DIARIA")),
            "ET_Dia_mm": extraer_numero(buscar("EVAPOTRANSPIRACION"))
        }

        # Guardar en CSV
        df = pd.DataFrame([registro])
        header = not os.path.exists(ARCHIVO_CSV)
        df.to_csv(ARCHIVO_CSV, mode='a', index=False, header=header, encoding='utf-8-sig')
        print(f"Captura realizada con éxito: {registro}")

        # Guardar gráficos solo a las 23hs
        if ahora.hour == 23:
            if not os.path.exists(CARPETA_GRAFICOS): os.makedirs(CARPETA_GRAFICOS)
            for g in ["temp.gif", "hum.gif", "baro.gif", "wind.gif", "rain.gif", "uv.gif", "solar.gif"]:
                try:
                    r_img = requests.get(BASE_URL_IMG + g, timeout=15)
                    with open(f"{CARPETA_GRAFICOS}/{ahora.strftime('%Y%m%d')}_{g}", 'wb') as f:
                        f.write(r_img.content)
                except: continue

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    capturar_todo()
