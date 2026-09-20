from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# Pagina configuratie
st.set_page_config(
    page_title="Het weer dashboard", page_icon="🌤️", layout="centered"
)

st.title("🌤️ Het weer dashboard (België)")
st.write(
    "Actueel weer, windrichting en een uurlijkse verwachting voor de komende uren."
)

# Sidebar voor locatie-instellingen met snelle Belgische steden
st.sidebar.header("📍 Locatie kiezen")

belgische_steden = {
    "Deinze (Standaard)": (50.9818, 3.5310),
    "Gent": (51.0543, 3.7174),
    "Brussel": (50.8503, 4.3517),
    "Antwerpen": (51.2194, 4.4025),
    "Brugge": (51.2093, 3.2247),
    "Kortrijk": (50.8280, 3.2649),
    "Hasselt": (50.9304, 5.3378),
    "Leuven": (50.8798, 4.7005),
}

gekozen_stad = st.sidebar.selectbox(
    "Kies een Belgische stad:", list(belgische_steden.keys())
)
default_lat, default_lon = belgische_steden[gekozen_stad]

lat = st.sidebar.number_input(
    "Breedtegraad (Latitude)", value=default_lat, format="%.4f"
)
lon = st.sidebar.number_input(
    "Lengtegraad (Longitude)", value=default_lon, format="%.4f"
)


# Functie om graden om te zetten naar windrichting (kompas)
def deg_to_compass(deg):
  if deg is None:
    return "-"
  val = int((deg / 22.5) + 0.5)
  arr = ["N", "NO", "O", "ZO", "Z", "ZW", "W", "NW"]
  return arr[(val // 2) % 8]


# 1. Functie voor 2-uurs neerslagverwachting (Buienradar raintext)
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


# 2. Functie voor actueel weer + uurlijkse verwachting via Open-Meteo
@st.cache_data(ttl=300)
def fetch_weather_data(lat, lon):
  url = (
      f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
      "&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,wind_direction_10m"
      "&hourly=temperature_2m,wind_speed_10m,wind_direction_10m"
  )
  try:
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
      return response.json()
  except Exception:
    pass
  return None


# Knop om te verversen
if st.button("🔄 Ververs Weergegevens", type="primary"):
  st.rerun()

# --- SECTIE 1: 2-UURS NEERSLAGVERWACHTING ---
st.subheader("⏱️ Neerslagverwachting komende 2 uur")

with st.spinner("Gegevens ophalen..."):
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

st.markdown("---")

# Data ophalen voor actueel en uurlijks
weather_data = fetch_weather_data(lat, lon)

if weather_data:
  # --- SECTIE 2: ACTUEEL WEER ---
  st.subheader(f"🌡️ Actueel Weer voor {gekozen_stad.split('(')[0].strip()}")
  if "current" in weather_data:
    current = weather_data["current"]
    wind_dir_deg = current.get("wind_direction_10m", 0)
    wind_dir_text = deg_to_compass(wind_dir_deg)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Temperatuur", f"{current.get('temperature_2m', 'N/B')} °C")
    col2.metric(
        "Gevoelstempr.", f"{current.get('apparent_temperature', 'N/B')} °C"
    )
    col3.metric(
        "Luchtvochtigheid", f"{current.get('relative_humidity_2m', 'N/B')}%"
    )
    col4.metric("Windsnelheid", f"{current.get('wind_speed_10m', 'N/B')} km/h")
    col5.metric("Windrichting", f"{wind_dir_text} ({wind_dir_deg}°)")

  st.markdown("---")

  # --- SECTIE 3: UURLIJKSE VERWACHTING (TABEL VOOR VOLGENDE 8 UUR) ---
  st.subheader("📋 Weersverwachting per uur (komende 8 uur)")

  if "hourly" in weather_data:
    hourly = weather_data["hourly"]
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    wind_speeds = hourly.get("wind_speed_10m", [])
    wind_dirs = hourly.get("wind_direction_10m", [])

    # Zoek het huidige uur om vanaf daar te beginnen
    now_str = datetime.now().strftime("%Y-%m-%dT%H:00")
    start_idx = 0
    for idx, t in enumerate(times):
      if t >= now_str:
        start_idx = idx
        break

    # Neem de komende 8 uur vanaf nu
    end_idx = start_idx + 8

    table_data = []
    for i in range(start_idx, min(end_idx, len(times))):
      # Format tijd naar enkel uur (bijv. "14:00")
      tijd_formaat = datetime.fromisoformat(times[i]).strftime("%H:%M")
      richting = deg_to_compass(wind_dirs[i])

      table_data.append({
          "Tijd": tijd_formaat,
          "Temperatuur (°C)": f"{temps[i]} °C",
          "Windsnelheid (km/h)": f"{wind_speeds[i]} km/h",
          "Windrichting": f"{richting} ({wind_dirs[i]}°)",
      })

    df_hourly = pd.DataFrame(table_data)
    st.dataframe(df_hourly, use_container_width=True, hide_index=True)
else:
  st.error(
      "Kon geen weerdata ophalen. Controleer je internetverbinding of API-limiet."
  )
