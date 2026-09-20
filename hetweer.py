from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# Pagina configuratie
st.set_page_config(
    page_title="Streamlit Buienradar & Buienalert", page_icon="🌧️", layout="centered"
)

st.title("🌧️ Buienradar & Buienalert Dashboard")
st.write(
    "Bekijk direct de neerslagverwachting voor de komende 2 uur en actuele weergegevens via de Buienradar API."
)

# Sidebar voor locatie-instellingen (Standaard coördinaten voor België/regio)
st.sidebar.header("📍 Locatie Instellingen")
lat = st.sidebar.number_input(
    "Breedtegraad (Latitude)", value=51.05, format="%.4f"
)
lon = st.sidebar.number_input("Lengtegraad (Longitude)", value=3.73, format="%.4f")
st.sidebar.caption(
    "Standaard ingesteld op Gent. Pas aan naar wens (bijv. Brussel = 50.85, 4.35)."
)


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
          # Waarde is neerslagintensiteit (mm/uur), formule Buienradar: 10^((val-109)/32) of direct 0 als 000
          try:
            rain_mm = (
              float(rain_val) if rain_val != "" else 0.0
            )  # Eenvoudige parsing
            # Officiële omrekening van buienradar tekstcode naar mm/u:
            # Als waarde 0 of leeg is = 0 mm/u. Anders: pow(10, (int(val) - 109) / 32)
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
  # Check of er regen wordt verwacht
  max_rain = df_rain["Neerslag (mm/u)"].max()
  if max_rain > 0:
    st.warning(
      "⚠️ **Buienalert:** Er is neerslag op komst in de gekozen regio!"
    )
  else:
    st.success("☀️ Droog: Er wordt de komende 2 uur geen neerslag verwacht.")

  # Grafiek tonen in Streamlit
  st.line_chart(df_rain.set_index("Tijd"))

  with st.expander("Bekijk ruwe data (tabel)"):
    st.dataframe(df_rain, use_container_width=True)
else:
  st.info(
    "Geen neerslagdata beschikbaar voor deze coördinaten of netwerkfout."
  )

st.markdown("---")

# --- SECTIE 2: ACTUEEL WEER (STATIONS) ---
st.subheader("🌡️ Actueel Weer (Algemeen Station)")

weather_json = fetch_weather_data()
if weather_json and "actual" in weather_json:
  stations = weather_json["actual"]["stationmeasurements"]
  # Kies het eerste station of zoek naar een specifiek station (bv. Melle/Zaventem)
  # Voor het gemak tonen we de eerste 5 stations of een selectie
  station_namen = [s["stationname"] for s in stations]

  selected_station_name = st.selectbox(
    "Kies een meetstation", station_namen, index=0
  )

  # Vind data van gekozen station
  station_data = next(
    s for s in stations if s["stationname"] == selected_station_name
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
    f"Laatst gemeten op: {station_data.get('measured', 'Onbekend')} | Bron:"
    " Buienradar.nl"
  )
