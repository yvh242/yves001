import folium
import gpxpy
import streamlit as st
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation

st.title("🚴 Fiets Tracker & Navigator")

# 1. GPX-bestand uploaden
uploaded_file = st.file_uploader("Upload je .gpx route", type=["gpx"])

route_coords = []
if uploaded_file:
  gpx = gpxpy.parse(uploaded_file)
  for track in gpx.tracks:
    for segment in track.segments:
      for point in segment.points:
        route_coords.append([point.latitude, point.longitude])

# 2. Huidige locatie van je telefoon ophalen
current_pos = streamlit_geolocation()

# 3. Bepaal het middelpunt van de kaart
# Als we een route hebben, starten we daar, anders bij je huidige locatie (of een standaardplek)
if route_coords:
  start_map_lat, start_map_lon = route_coords[0]
elif current_pos and current_pos.get("latitude"):
  start_map_lat, start_map_lon = (
      current_pos["latitude"],
      current_pos["longitude"],
  )
else:
  start_map_lat, start_map_lon = 51.0543, 3.5350  # Standaard (bijv. Deinze)

# Maak ÉÉN enkele Folium kaart aan
m = folium.Map(location=[start_map_lat, start_map_lon], zoom_start=13)

# Voeg de GPX-route toe aan de kaart (als blauwe lijn)
if route_coords:
  folium.PolyLine(
      route_coords, color="blue", weight=5, tooltip="Jouw Route"
  ).add_to(m)

# Voeg jouw live locatie toe aan dezelfde kaart (als rode marker)
if current_pos and current_pos.get("latitude") and current_pos.get("longitude"):
  user_lat = current_pos["latitude"]
  user_lon = current_pos["longitude"]

  folium.Marker(
      [user_lat, user_lon],
      popup="Jouw Huidige Locatie",
      icon=folium.Icon(color="red", icon="bicycle", prefix="fa"),
  ).add_to(m)

  st.success("Live locatie gevonden!")
else:
  st.info("Wachten op live GPS-locatie...")

# 4. Toon de gecombineerde kaart in Streamlit
st_folium(m, width=700, height=500)
