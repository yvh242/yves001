from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# Pagina configuratie
st.set_page_config(
    page_title="Het weer dashboard", page_icon="🌤️", layout="wide"
)

# --- MODERNE STYLING (CUSTOM CSS) ---
st.markdown("""
    <style>
    /* Algemene aanpassingen voor een strakkere look */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    /* Stijl voor metrische kaarten */
    div[data-testid="stMetric"] {
        background-color: rgba(28, 131, 246, 0.04);
        border: 1px solid rgba(28, 131, 246, 0.1);
        padding: 15px 15px 10px 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    div[data-testid="stMetric"] label {
        font-size: 0.85rem !important;
        color: #555;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌤️ Het weer dashboard")
st.caption("Actueel weer, neerslag en uitgebreide verwachtingen voor België.")

# --- LOCATIE KEUZE BOVENAAN ---
with st.container(border=True):
  col_l1, col_l2 = st.columns([3, 1])
  with col_l1:
    ingevoerde_plaats = st.text_input(
        "🔍 Zoek een plaats of gemeente in België",
        value="Deinze",
        help="Typ een plaatsnaam en druk op enter",
    )


# Functie om coördinaten automatisch op te zoeken via Open-Meteo Geocoding API
@st.cache_data(ttl=3600)
def zoek_coordinaten(plaatsnaam):
  url = f"https://geocoding-api.open-meteo.com/v1/search?name={plaatsnaam}&count=1&language=nl&format=json"
  try:
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
      data = response.json()
      if "results" in data and len(data["results"]) > 0:
        res = data["results"][0]
        return res["latitude"], res["longitude"], res.get("name", plaatsnaam)
  except Exception:
    pass
  return None, None, None


lat, lon, locatie_naam = zoek_coordinaten(ingevoerde_plaats)

if lat is None or lon is None:
  st.warning(
      f"Kon '{ingevoerde_plaats}' niet vinden. We vallen terug op Deinze."
  )
  lat, lon, locatie_naam = (50.9818, 3.5310, "Deinze")
else:
  st.success(
      f"Geselecteerde locatie: **{locatie_naam}** (automatisch gelokaliseerd)"
  )


# Functie om graden om te zetten naar windrichting
def deg_to_compass(deg):
  if deg is None:
    return "-"
  val = int((deg / 22.5) + 0.5)
  arr = ["N", "NO", "O", "ZO", "Z", "ZW", "W", "NW"]
  return arr[(val // 2) % 8]


# API functies
def fetch_rain_forecast(lat, lon):
  url = f"https://gpsgadget.buienradar.nl/data/raintext?lat={lat}&lon={lon}"
  try:
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
      lines = response.text.strip().split("\n")
      data = []
      for line in lines:
        parts = line.split("|")
        if len(parts) == 2:
          rain_val, time_val = parts
          try:
            val_int = int(rain_val)
            if val_int <= 0:
              mm_h = 0.0
            else:
              mm_h = round(10 ** ((val_int - 109) / 32), 2)
          except:
            mm_h = 0.0
          data.append({"Tijd": time_val, "Neerslag (mm/u)": mm_h})
      return pd.DataFrame(data)
  except Exception:
    pass
  return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_weather_data(lat, lon):
  url = (
      f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
      "&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,wind_direction_10m"
      "&hourly=temperature_2m,wind_speed_10m,wind_direction_10m,precipitation"
      "&daily=temperature_2m_max,temperature_2m_min,weathercode"
      "&timezone=auto"
  )
  try:
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
      return response.json()
  except Exception:
    pass
  return None


# --- STREAMLIT TABS ---
tab1, tab2 = st.tabs(["⏱️ Vandaag & Uurlijks", "📅 14-daagse verwachting"])

weather_data = fetch_weather_data(lat, lon)

with tab1:
  # Sectie: Neerslag komende 2 uur + Buienradar link
  with st.container(border=True):
    col_r1, col_r2 = st.columns([3, 1])
    with col_r1:
      st.subheader("⏱️ Neerslagverwachting komende 2 uur")
    with col_r2:
      st.markdown(
          "<div style='text-align: right; padding-top: 5px;'><a"
          " href='https://www.buienradar.be/' target='_blank'>🔗 Ga naar"
          " Buienradar.be</a></div>",
          unsafe_allow_html=True,
      )

    df_rain = fetch_rain_forecast(lat, lon)
    if not df_rain.empty:
      max_rain = df_rain["Neerslag (mm/u)"].max()
      if max_rain > 0:
        st.warning("⚠️ **Buienalert:** Er is neerslag op komst in deze regio!")
      else:
        st.success("☀️ Droog: Geen neerslag verwacht de komende 2 uur.")
      st.line_chart(df_rain.set_index("Tijd"))
    else:
      st.info("Geen neerslagdata beschikbaar.")

  # Sectie: Actueel weer
  if weather_data:
    with st.container(border=True):
      st.subheader(f"🌡️ Actueel Weer voor {locatie_naam}")
      if "current" in weather_data:
        current = weather_data["current"]
        wind_dir_deg = current.get("wind_direction_10m", 0)
        wind_dir_text = deg_to_compass(wind_dir_deg)

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Temperatuur", f"{current.get('temperature_2m', 'N/B')} °C")
        col2.metric(
            "Gevoelstemp.", f"{current.get('apparent_temperature', 'N/B')} °C"
        )
        col3.metric(
            "Luchtvochtigheid", f"{current.get('relative_humidity_2m', 'N/B')}%"
        )
        col4.metric(
            "Windsnelheid", f"{current.get('wind_speed_10m', 'N/B')} km/h"
        )
        col5.metric("Windrichting", f"{wind_dir_text} ({wind_dir_deg}°)")

    # Sectie: Uurlijkse verwachting (8 uur)
    with st.container(border=True):
      st.subheader("📋 Weersverwachting en neerslag per uur (komende 8 uur)")
      if "hourly" in weather_data:
        hourly = weather_data["hourly"]
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        wind_speeds = hourly.get("wind_speed_10m", [])
        wind_dirs = hourly.get("wind_direction_10m", [])
        precips = hourly.get("precipitation", [])

        now_str = datetime.now().strftime("%Y-%m-%dT%H:00")
        start_idx = 0
        for idx, t in enumerate(times):
          if t >= now_str:
            start_idx = idx
            break

        end_idx = start_idx + 8
        table_data = []
        for i in range(start_idx, min(end_idx, len(times))):
          tijd_formaat = datetime.fromisoformat(times[i]).strftime("%H:%M")
          richting = deg_to_compass(wind_dirs[i])
          neerslag_val = precips[i] if i < len(precips) else 0.0

          table_data.append({
              "Tijd": tijd_formaat,
              "Temperatuur (°C)": f"{temps[i]} °C",
              "Neerslag (mm)": f"{neerslag_val} mm",
              "Windsnelheid (km/h)": f"{wind_speeds[i]} km/h",
              "Windrichting": f"{richting} ({wind_dirs[i]}°)",
          })

        df_hourly = pd.DataFrame(table_data)
        st.dataframe(df_hourly, use_container_width=True, hide_index=True)

with tab2:
  with st.container(border=True):
    st.subheader(f"📅 14-daagse verwachting voor {locatie_naam}")

    if weather_data and "daily" in weather_data:
      daily = weather_data["daily"]
      dates = daily.get("time", [])
      max_temps = daily.get("temperature_2m_max", [])
      min_temps = daily.get("temperature_2m_min", [])
      codes = daily.get("weathercode", [])

      dag_namen = {
          "Mon": "Ma",
          "Tue": "Di",
          "Wed": "Wo",
          "Thu": "Do",
          "Fri": "Vr",
          "Sat": "Za",
          "Sun": "Zo",
      }

      def get_weather_desc(code):
        if code in [0]:
          return "☀️ Zonnig"
        elif code in [1, 2, 3]:
          return "⛅ Licht bewolkt"
        elif code in [45, 48]:
          return "🌫️ Mist"
        elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
          return "🌧️ Regen"
        elif code in [71, 73, 75, 85, 86]:
          return "❄️ Sneeuw"
        else:
          return "☁️ Bewolkt"

      daily_rows = []

      for i in range(len(dates)):
        dt = datetime.fromisoformat(dates[i])
        eng_dag = dt.strftime("%a")
        nl_dag = dag_namen.get(eng_dag, eng_dag)
        datum_str = dt.strftime("%d-%m")
        weer_tekst = get_weather_desc(codes[i] if i < len(codes) else 0)

        daily_rows.append({
            "Dag": nl_dag,
            "Datum": datum_str,
            "Weer": weer_tekst,
            "Max Temp (°C)": f"{max_temps[i]}°C",
            "Min Temp (°C)": f"{min_temps[i]}°C",
        })

      df_daily = pd.DataFrame(daily_rows)
      st.dataframe(df_daily, use_container_width=True, hide_index=True)
    else:
      st.info("Geen 14-daagse verwachting beschikbaar.")
