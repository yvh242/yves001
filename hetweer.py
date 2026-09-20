from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# Pagina configuratie
st.set_page_config(
    page_title="Het weer dashboard", page_icon="🌤️", layout="centered"
)

st.title("🌤️ Het weer dashboard")
st.write(
    "Bekijk de neerslagverwachting voor de komende 2 uur en het actuele weer in België via de Buienradar API."
)

# Sidebar voor locatie-instellingen (Standaard ingesteld op Deinze, BE)
st.sidebar.header("📍 Locatie Instellingen")
lat = st.sidebar.number_input(
    "Breedtegraad (Latitude)", value=50.9818, format="%.4f"
)
lon = st.sidebar.number_input(
    "Lengtegraad (Longitude)", value=3.5310, format="%.4f"
)
st.sidebar.caption("Standaard ingesteld op 9850 Deinze (50.9818, 3.5310).")


# Functie om neerslagdata op te halen (raintext endpoint)
def fetch_rain_forecast(lat, lon):
  url = f"https://gpsgadget.buienradar.nl/data/raintext?lat={lat}&lon={lon}"
  try:
    response = requests.get(url)
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
  except Exception as e:
    st.error(f"Fout bij ophalen neerslagdata: {e}")
  return pd.DataFrame()


# Functie om actuele weerdata op te halen (JSON feed)
@st.cache_data(ttl=300)  # Cache voor 5 minuten
def fetch_weather_data():
  url = "https://data.buienradar.nl/2.0/feed/json"
  try:
    response = requests.get(url)
    if response.status_code == 200:
      return response.json()
  except Exception as e:
    st.error(f"Fout bij ophalen weerfeed: {e}")
  return None


# Data ophalen knop
if st.button("🔄 Ververs Weergegevens", type="primary"):
  st.rerun()

# --- SECTIE 1: 2-UURS NEERSLAGVERWACHTING (BUIENALERT) ---
st.subheader("⏱️ Neerslagverwachting komende 2 uur")

with st.spinner("Neerslagradar ophalen..."):
  df_rain = fetch_rain_forecast(lat, lon)

if not df_rain.empty:
  max_rain = df_rain["Neerslag (mm/u)"].max()
  if max_rain > 0:
    st.warning(
      "⚠️ **Buienalert:** Er is neerslag op komst in de gekozen regio!"
    )
  else:
    st.success("☀️ Droog: Er wordt de komende 2 uur geen neerslag verwacht.")

  st.line_chart(df_rain.set_index("Tijd"))

  with st.expander("Bekijk ruwe data (tabel)"):
    st.dataframe(df_rain, use_container_width=True)
else:
  st.info(
    "Geen neerslagdata beschikbaar voor deze coördinaten of netwerkfout."
  )

st.markdown("---")

# --- SECTIE 2: ACTUEEL WEER (BELGISCHE STATIONS) ---
st.subheader("🌡️ Actueel Weer in België")

weather_json = fetch_weather_data()
if weather_json and "actual" in weather_json:
  stations = weather_json["actual"]["stationmeasurements"]

  # Filter specifiek op Belgische stations (country == 'BE') of op naam
  belgian_stations = [
      s for s in stations if s.get("country", "").upper() == "BE"
  ]

  # Als fallback alle stations tonen als de 'country' tag ontbreekt
  active_station_list = belgian_stations if belgian_stations else stations

  station_namen = [s["stationname"] for s in active_station_list]

  # Zoekbalk/selectie box specifiek voor Belgische meetstations (met automatische sortering)
  station_namen.sort()

  # Zet standaard selectie op 'Melle' of 'Gent' als deze in de lijst staat, anders de eerste
  default_idx = 0
  for idx, name in enumerate(station_namen):
    if "melle" in name.lower() or "gent" in name.lower():
      default_idx = idx
      break

  selected_station_name = st.selectbox(
      "Zoek of kies een meetstation in België",
      station_namen,
      index=default_idx,
  )

  # Data van gekozen station ophalen
  station_data = next(
      s for s in active_station_list if s["stationname"] == selected_station_name
  )

  col1, col2, col3, col4 = st.columns(4)
  col1.metric("Temperatuur", f"{station_data.get('temperature', 'N/B')} °C")
  col2.metric(
      "Gevoelstemperatuur", f"{station_data.get('feeltemperature', 'N/B')} °C"
  )
  col3.metric(
      "Luchtvochtigheid", f"{station_data.get('humidity', 'N/B')}%"
  )
  col4.metric(
      "Windkracht", f"{station_data.get('windforce', 'N/B')} Bft"
  )

  st.caption(
      f"Meetstation: {station_data.get('stationname')} | Laatst gemeten op:"
      f" {station_data.get('measured', 'Onbekend')} | Bron: Buienradar.nl"
  )
