# Clima San Isidro — Monitor Automático

Captura automática de datos meteorológicos de la **Estación Meteorológica Automática (EMA)** del Hipódromo de San Isidro, publicados en:

> https://hipodromosanisidro.com/clima/mb3uv.htm

---

## ¿Qué captura?

### Datos numéricos → `registro_clima_san_isidro.csv`

| Columna | Descripción |
|---|---|
| `Fecha_Hora` | Timestamp de la captura (YYYY-MM-DD HH:MM:SS) |
| `Temperatura_C` | Temperatura en °C |
| `Humedad_pct` | Humedad relativa en % |
| `Punto_Rocio_C` | Punto de rocío en °C |
| `Presion_hPa` | Presión barométrica en hPa |
| `Radiacion_Solar_Wm2` | Radiación solar en W/m² |
| `Indice_UV` | Índice UV |
| `Viento_Velocidad_kmh` | Velocidad del viento en km/h |
| `Viento_Direccion` | Dirección cardinal del viento (N, NE, S…) |
| `Lluvia_Dia_mm` | Lluvia acumulada del día en mm |
| `ET_Dia_mm` | Evapotranspiración del día en mm |

### Gráficos → carpeta `graficos/`

Descarga automáticamente los gráficos publicados por la estación:
- Temperatura y humedad 24h
- Lluvia, viento, presión, radiación solar, UV, ET — 24h
- Rosa de vientos
- Resumen diario
- Gráficos mensuales y anuales (si el servidor los publica)

---

## Frecuencia

Cada **3 horas** vía GitHub Actions (cron `45 */3 * * *`).
También puede lanzarse manualmente desde la pestaña **Actions → Run workflow**.

---

## Uso local

```bash
pip install pandas requests beautifulsoup4 lxml
python captura_clima.py
```

---

## Estructura del repositorio

```
.
├── captura_clima.py                  # Script principal
├── registro_clima_san_isidro.csv     # Datos acumulados
├── graficos/                         # Gráficos descargados
└── .github/workflows/daily_scrape.yml
```
