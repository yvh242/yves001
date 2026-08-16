import math
import folium
import gpxpy
import streamlit as st
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(page_title="Fiets Tracker", page_icon="🚴", layout="centered")

st.title("🚴 Fiets Tracker & Navigator")

# 1. Haversine functie voor afstandsberekening
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Aarde radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# 2. GPX-bestand uploaden en verwerken
uploaded_file = st.file_uploader("Upload je .gpx route", type=["gpx"])
route_coords = []
waypoints = []

if uploaded_file:
    gpx = gpxpy.parse(uploaded_file)
    # Haal routepad op
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                route_coords.append([point.latitude, point.longitude])
    # Haal waypoints op
    for wp in gpx.waypoints:
        waypoints.append({'name': wp.name or "Onbekend punt", 'lat': wp.latitude, 'lon': wp.longitude})

# 3. Live locatie ophalen
current_pos = streamlit_geolocation()

# 4. Kaart opbouwen
if route_coords:
    center = route_coords[0]
else:
    center = [51.0543, 3.5350] # Default fallback

m = folium.Map(location=center, zoom_start=14)

# Voeg route toe
if route_coords:
    folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.7).add_to(m)

# Voeg waypoints toe
for wp in waypoints:
    folium.Marker([wp['lat'], wp['lon']], icon=folium.Icon(color="green", icon="info-sign")).add_to(m)

# Voeg eigen locatie toe
if current_pos and current_pos.get("latitude"):
    user_lat = current_pos["latitude"]
    user_lon = current_pos["longitude"]
    folium.Marker(
        [user_lat, user_lon],
        popup="Jouw Locatie",
        icon=folium.Icon(color="red", icon="bicycle", prefix="fa"),
    ).add_to(m)
    
    # Navigatie-assistent (afstand tot dichtstbijzijnde waypoint)
    if waypoints:
        closest_wp = min(waypoints, key=lambda wp: haversine_distance(user_lat, user_lon, wp['lat'], wp['lon']))
        dist = haversine_distance(user_lat, user_lon, closest_wp['lat'], closest_wp['lon'])
        st.subheader("📍 Navigatie-assistent")
        st.info(f"Nog **{int(dist)} meter** tot: **{closest_wp['name']}**")
    
    st.success("Live locatie actief.")
else:
    st.warning("Wachten op GPS-locatie...")

# 5. Kaart tonen
st_folium(m, width=700, height=500)

# Ververs knop
if st.button("Ververs kaart"):
    st.rerun()
app.py
app.py weergeven.
