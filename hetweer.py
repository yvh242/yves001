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
    "Bekijk de neerslagverwachting en het actuele weer via officiële Belgische meetstations (KMI / Meteo.be)."
)

# Sidebar voor locatie-instellingen (Standaard ingesteld op Deinze, BE)
st.sidebar.header("📍 Locatie Neerslagradar")
lat = st.sidebar.number_input(
    "Breedtegraad (Latitude)", value=50.9818, format="%.4f"
)
lon = st.sidebar.number_input(
    "Lengtegraad (Longitude)", value=3.5310, format="%.4f"
)
st.sidebar.caption("Standaard ingesteld op 9850 Deinze (50.9818, 3.5310).")


# Functie om neerslagdata op te halen (Buienradar raintext werkt prima wereldwijd op coördinaten)
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


# Functie om actuele weerdata op te halen via de publieke KMI/Meteo.be API
@st.cache_data(ttl=300)
def fetch_kmi_weather():
  # Publiek endpoint van de officiële KMI/Meteo app
  url = "https://app.meteo.be/api/v1/obs"
  try:
    response = requests.get(url)
    if response.status_code == 200:
      return response.json()
  except Exception as e:
    st.error(f"Fout bij ophalen KMI weerdata: {e}")
  return None


# Data ophalen knop
if st.button("🔄 Ververs Weergegevens", type="primary"):
  st.rerun()

# --- SECTIE 1: 2-UURS NEERSLAGVERWACHTING ---
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
    st.info("Geen neerslagdata beschikbaar voor deze coördinaten.")

st.markdown("---")

# --- SECTIE 2: ACTUEEL WEER (KMI / BELGISCHE STATIONS) ---
st.subheader("🌡️ Actueel Weer in België (KMI Meetstations)")

kmi_data = fetch_kmi_weather()

if kmi_data:
  # De structuur van de KMI API bevat een lijst van stations met observaties
  stations = kmi_data if isinstance(kmi_data, list) else kmi_data.get("stations", [])

  # Als stations in een ander formaat zitten, vangen we dit op
  if not stations and isinstance(kmi_data, dict):
    # Zoek naar stations sleutel of iterus
    stations = kmi_data.get("data", [])

  # Bouw een dictionary op basis van de stationsnamen (bijv. Melle, Beitem, Ukkel)
  station_dict = {}
  for s in stations:
    # KMI gebruikt vaak 'name' of 'stationName'
    name = s.get("name") or s.get("stationName") or s.get("title", "Onbekend")
    station_dict[name] = s

  if station_dict:
    sorted_stations = sorted(list(station_dict.keys()))

    # Zet Melle of de dichtstbijzijnde als standaard indien aanwezig
    default_idx = 0
    for idx, name in enumerate(sorted_stations):
      if "melle" in name.lower() or "gent" in name.lower():
        default_idx = idx
        break

    selected_station = st.selectbox(
        "Kies een Belgisch meetstation (KMI):",
        sorted_stations,
        index=default_idx,
    )

    s_data = station_dict[selected_station]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Temperatuur", f"{s_data.get('temperature', s_data.get('temp', 'N/B'))} °C")
    col2.metric("Gevoelstempr.", f"{s_data.get('feelTemperature', s_data.get('apparent_temp', 'N/B'))} °C")
    col3.metric("Luchtvochtigheid", f"{s_data.get('humidity', 'N/B')}%")
    col4.metric("Windkracht", f"{s_data.get('windForce', s_data.get('wind_speed', 'N/B'))}")

    st.caption(
        f"Bron: Officiële KMI / Meteo.be metingen voor station: {selected_station}"
    )
  else:
    st.info("Kon geen stationslijst parsen uit de KMI feed.")
else:
  st.warning("Kan geen verbinding maken met de KMI/Meteo.be server.")
