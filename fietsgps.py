import streamlit as st
import gpxpy
import pandas as pd
from streamlit_geolocation import streamlit_geolocation

# 1. GPX Bestand uploaden
uploaded_file = st.file_uploader("Upload je .gpx route", type=["gpx"])

if uploaded_file:
    # GPX parsen
    gpx = gpxpy.parse(uploaded_file)
    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append({'lat': point.latitude, 'lon': point.longitude})
    
    route_df = pd.DataFrame(points)
    
    # 2. Huidige locatie ophalen
    current_pos = streamlit_geolocation()
    
    # 3. Kaart tonen
    st.write("Route en jouw positie:")
    # Gebruik st.map met beide datasets
    st.map(route_df) # Dit toont de lijn van de route
    
    if current_pos['latitude']:
        user_df = pd.DataFrame({'lat': [current_pos['latitude']], 'lon': [current_pos['longitude']]})
        st.map(user_df) # Dit toont jouw stip op de kaart
