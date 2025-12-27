import streamlit as st
import pandas as pd
import kagglehub
import os
import random

# --- VERTALINGEN ---
continent_vertaling = {
    "Africa": "Afrika",
    "Antarctica": "Antarctica",
    "Asia": "Azië",
    "Europe": "Europa",
    "North America": "Noord-Amerika",
    "Oceania": "Oceanië",
    "South America": "Zuid-Amerika"
}

# --- DATA LADEN ---
@st.cache_data
def load_data():
    try:
        path = kagglehub.dataset_download("nikitagrec/world-capitals-gps")
        files = [f for f in os.listdir(path) if f.endswith('.csv')]
        if not files: return None
        
        df = pd.read_csv(os.path.join(path, files[0]))
        mapping = {
            'CountryName': 'Country', 
            'CapitalName': 'Capital', 
            'ContinentName': 'Continent'
        }
        df = df.rename(columns=mapping)
        # Vertaal de continenten in de dataframe
        df['Continent'] = df['Continent'].map(continent_vertaling).fillna(df['Continent'])
        return df[['Country', 'Capital', 'Continent']].dropna().reset_index(drop=True)
    except Exception as e:
        st.error(f"Fout bij laden: {e}")
        return None

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

# --- UI & FILTERS ---
st.set_page_config(page_title="Continent Quiz NL", page_icon="🌎")
st.title("🌍 Hoofdsteden Quiz")

# Stap 1: Selectie (alleen tonen als quiz NIET gestart is)
if not st.session_state.quiz_gestart:
    st.subheader("Selecteer de continenten die je wilt oefenen:")
    all_continents = sorted(df_full['Continent'].unique().tolist())
    selected_continents = st.multiselect(
        "Kies één of meerdere:",
        options=all_continents,
        default=all_continents
    )
    
    if st.button("🚀 Start de Quiz", use_container_width=True):
        if selected_continents:
            st.session_state.selected_continents = selected_continents
            st.session_state.quiz_gestart = True
            st.rerun()
        else:
            st.warning("Kies minimaal één continent!")

# Stap 2: De Quiz (tonen als quiz gestart is)
else:
    df_filtered = df_full[df_full['Continent'].isin(st.session_state.selected_continents)].reset_index(drop=True)

    # Sidebar info
    st.sidebar.header("📊 Voortgang")
    st.sidebar.metric("Score", st.session_state.score)
    st.sidebar.write(f"Geselecteerd: {', '.join(st.session_state.selected_continents)}")
    
    if st.sidebar.button("⏹ Stop Quiz"):
        st.session_state.quiz_gestart = False
        st.session_state.score = 0
        st.session_state.current_idx = None
        st.rerun()

    if st.session_state.current_idx is None:
        prepare_new_card(df_filtered)

    current_row = df_filtered.iloc[st.session_state.current_idx]
    
    st.markdown(f"### Wat is de hoofdstad van **{current_row['Country']}**?")
    st.caption(f"🌍 Continent: {current_row['Continent']}")

    # Knoppen
    for option in st.session_state.options:
        if st.button(option, key=f"btn_{option}", use_container_width=True):
            if option == current_row['Capital']:
                st.session_state.feedback = ("success", f"✅ Juist! Het is {option}.")
                st.session_state.score += 1
                st.balloons()
            else:
                st.session_state.attempts += 1
                if st.session_state.attempts < 2:
                    st.session_state.feedback = ("warning", "❌ Fout. Je hebt nog één poging!")
                else:
                    st.session_state.feedback = ("error", f"💥 Helaas. Het juiste antwoord was: {current_row['Capital']}")

    # Feedback en Volgende
    if st.session_state.feedback:
        type, msg = st.session_state.feedback
        if type == "success": st.success(msg)
        elif type == "warning": st.warning(msg)
        else: st.error(msg)

        if type == "success" or st.session_state.attempts >= 2:
            if st.button("Volgende Land ➡️"):
                prepare_new_card(df_filtered)
                st.rerun()
