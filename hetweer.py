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
    "Actueel weer en neerslagverwachting via betrouwbare open-source weerdata."
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


# 2. Functie voor actueel weer via Open-Meteo (altijd stabiel in België)
@st.cache_data(ttl=300)
def fetch_current_weather(lat, lon):
  url = (
      f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m"
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

# --- SECTIE 2: ACTUEEL WEER (OPEN-METEO) ---
st.subheader(f"🌡️ Actueel Weer voor {gekozen_stad.split('(')[0].strip()}")

weather_data = fetch_current_weather(lat, lon)

if weather_data and "current" in weather_data:
  current = weather_data["current"]

  col1, col2, col3, col4 = st.columns(4)
  col1.metric("Temperatuur", f"{current.get('temperature_2m', 'N/B')} °C")
  col2.metric(
      "Gevoelstempr.", f"{current.get('apparent_temperature', 'N/B')} °C"
  )
  col3.metric(
      "Luchtvochtigheid", f"{current.get('relative_humidity_2m', 'N/B')}%"
  )
  col4.metric("Windsnelheid", f"{current.get('wind_speed_10m', 'N/B')} km/h")

  st.caption("Bron: Open-Meteo (Weerdata voor geselecteerde coördinaten)")
else:
  st.error(
      "Kon geen actuele weerdata ophalen. Controleer je internetverbinding."
  )
