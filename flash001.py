import streamlit as st
import pandas as pd
import kagglehub
import os
import random
import pycountry
import gettext
import pydeck as pdk

# --- VERTALINGS LOGICA ---
def translate_country(en_name):
    try:
        country = pycountry.countries.search_fuzzy(en_name)[0]
        dutch = gettext.translation('iso3166', pycountry.LOCALES_DIR, languages=['nl'])
        dutch.install()
        return _(country.name)
    except:
        return en_name

continent_vertaling = {
    "Africa": "Afrika", "Antarctica": "Antarctica", "Asia": "Azië",
    "Europe": "Europa", "Noord-Amerika": "North America", # Voor de zekerheid beide kanten
    "North America": "Noord-Amerika", "Oceania": "Oceanië", "South America": "Zuid-Amerika"
}

# --- DATA LADEN ---
@st.cache_data
def load_data():
    path = kagglehub.dataset_download("nikitagrec/world-capitals-gps")
    files = [f for f in os.listdir(path) if f.endswith('.csv')]
    df = pd.read_csv(os.path.join(path, files[0]))
    
    # Hernoem kolommen naar bruikbare namen
    df = df.rename(columns={
        'CountryName': 'Country', 
        'CapitalName': 'Capital', 
        'ContinentName': 'Continent',
        'CapitalLatitude': 'lat', 
        'CapitalLongitude': 'lon'
    })
    
    # Vertalingen
    df['Continent'] = df['Continent'].map(continent_vertaling).fillna(df['Continent'])
    unique_countries = df['Country'].unique()
    country_map = {name: translate_country(name) for name in unique_countries}
    df['Country'] = df['Country'].map(country_map)
    
    return df[['Country', 'Capital', 'Continent', 'lat', 'lon']].dropna().reset_index(drop=True)

df_full = load_data()

# --- SESSIE BEHEER ---
if 'quiz_gestart' not in st.session_state:
    st.session_state.quiz_gestart = False
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = None
if 'attempts' not in st.session_state:
    st.session_state.attempts = 0
if 'options' not in st.session_state:
    st.session_state.options = []
if 'feedback' not in st.session_state:
    st.session_state.feedback = None

def prepare_new_card(filtered_df):
    if filtered_df.empty: return
    st.session_state.current_idx = random.randint(0, len(filtered_df) - 1)
    st.session_state.attempts = 0
    st.session_state.feedback = None
    
    correct_answer = filtered_df.iloc[st.session_state.current_idx]['Capital']
    wrong_answers = df_full[df_full['Capital'] != correct_answer]['Capital'].sample(3).tolist()
    
    options = wrong_answers + [correct_answer]
    random.shuffle(options)
    st.session_state.options = options

# --- UI ---
st.set_page_config(page_title="Topografie Master", layout="wide")

if not st.session_state.quiz_gestart:
    st.title("🌎 Welkom bij de Wereld Quiz")
    all_continents = sorted(df_full['Continent'].unique().tolist())
    selected = st.multiselect("Kies je continenten:", all_continents, default=["Europa"])
    
    if st.button("🚀 Start de Quiz", use_container_width=True):
        if selected:
            st.session_state.selected_continents = selected
            st.session_state.quiz_gestart = True
            st.rerun()
        else:
            st.warning("Kies eerst een continent.")
else:
    df_filtered = df_full[df_full['Continent'].isin(st.session_state.selected_continents)].reset_index(drop=True)
    
    if st.session_state.current_idx is None:
        prepare_new_card(df_filtered)

    row = df_filtered.iloc[st.session_state.current_idx]

    # Layout met twee kolommen: Kaart links, Vragen rechts
    col_map, col_quiz = st.columns([2, 1])

    with col_map:
        # De kaart focussen op de hoofdstad
        view_state = pdk.ViewState(
            latitude=row['lat'],
            longitude=row['lon'],
            zoom=3,
            pitch=0
        )
        
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=pd.DataFrame([row]),
            get_position='[lon, lat]',
            get_color='[200, 30, 0, 160]',
            get_radius=200000,
        )

        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            # Gebruik 'road' of 'satellite' (zonder de mapbox:// prefix) 
            # of laat het weg voor de standaard CartoDB stijl
            map_style=None 
        ))  

    with col_quiz:
        st.subheader(f"Wat is de hoofdstad van:")
        st.header(f"📍 {row['Country']}")
        st.write(f"Continent: *{row['Continent']}*")
        st.divider()

        for option in st.session_state.options:
            if st.button(option, key=option, use_container_width=True):
                if option == row['Capital']:
                    st.session_state.feedback = ("success", f"✅ Goed! Het is {option}.")
                    st.session_state.score += 1
                    st.balloons()
                else:
                    st.session_state.attempts += 1
                    if st.session_state.attempts < 2:
                        st.session_state.feedback = ("warning", "❌ Fout. Nog één poging!")
                    else:
                        st.session_state.feedback = ("error", f"💥 Helaas. Het was {row['Capital']}.")

        if st.session_state.feedback:
            t, m = st.session_state.feedback
            getattr(st, t)(m)
            if t == "success" or st.session_state.attempts >= 2:
                if st.button("Volgende Land ➡️", use_container_width=True):
                    prepare_new_card(df_filtered)
                    st.rerun()

    # Sidebar Stopknop
    st.sidebar.metric("Score", st.session_state.score)
    if st.sidebar.button("⏹ Stop Quiz"):
        st.session_state.quiz_gestart = False
        st.session_state.score = 0
        st.session_state.current_idx = None
        st.rerun()
