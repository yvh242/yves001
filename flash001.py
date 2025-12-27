import streamlit as st
import pandas as pd
import kagglehub
import os
import random

# --- DATA LADEN ---
@st.cache_data
def load_data():
    try:
        path = kagglehub.dataset_download("nikitagrec/world-capitals-gps")
        files = [f for f in os.listdir(path) if f.endswith('.csv')]
        if not files: return None
        
        df = pd.read_csv(os.path.join(path, files[0]))
        # Mapping voor kolommen
        mapping = {
            'CountryName': 'Country', 
            'CapitalName': 'Capital', 
            'ContinentName': 'Continent'
        }
        df = df.rename(columns=mapping)
        return df[['Country', 'Capital', 'Continent']].dropna().reset_index(drop=True)
    except Exception as e:
        st.error(f"Fout bij laden: {e}")
        return None

df_full = load_data()

# --- SESSIE BEHEER ---
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
    if filtered_df.empty:
        return
    st.session_state.current_idx = random.randint(0, len(filtered_df) - 1)
    st.session_state.attempts = 0
    st.session_state.feedback = None
    
    correct_answer = filtered_df.iloc[st.session_state.current_idx]['Capital']
    # Pak foute antwoorden uit de HELE dataset voor meer variatie
    wrong_answers = df_full[df_full['Capital'] != correct_answer]['Capital'].sample(3).tolist()
    
    options = wrong_answers + [correct_answer]
    random.shuffle(options)
    st.session_state.options = options

# --- UI & FILTERS ---
st.set_page_config(page_title="Continent Quiz Master", page_icon="🌎")
st.title("🌍 Capital Quiz per Continent")

# Sidebar voor instellingen
st.sidebar.header("⚙️ Instellingen")
all_continents = sorted(df_full['Continent'].unique().tolist())
selected_continents = st.sidebar.multiselect(
    "Kies continenten om uit te quizzen:",
    options=all_continents,
    default=all_continents
)

# Filter de dataframe
df_filtered = df_full[df_full['Continent'].isin(selected_continents)].reset_index(drop=True)

st.sidebar.divider()
st.sidebar.metric("Totaal Score", st.session_state.score)

# Controleer of er data is na filtering
if df_filtered.empty:
    st.warning("Selecteer minimaal één continent in de zijbalk om te beginnen.")
else:
    # Initialiseer eerste kaart als dat nog niet is gebeurd
    if st.session_state.current_idx is None or st.session_state.current_idx >= len(df_filtered):
        prepare_new_card(df_filtered)

    # Quiz kaart
    current_row = df_filtered.iloc[st.session_state.current_idx]
    
    st.markdown(f"### Wat is de hoofdstad van **{current_row['Country']}**?")
    st.caption(f"📍 Regio: {current_row['Continent']}")

    # Meerkeuze knoppen
    for option in st.session_state.options:
        if st.button(option, key=f"btn_{option}", use_container_width=True):
            if option == current_row['Capital']:
                st.session_state.feedback = ("success", f"✅ Correct! Het is {option}.")
                st.session_state.score += 1
                st.balloons()
            else:
                st.session_state.attempts += 1
                if st.session_state.attempts < 2:
                    st.session_state.feedback = ("warning", "❌ Helaas! Probeer het nog één keer.")
                else:
                    st.session_state.feedback = ("error", f"💥 Geen pogingen meer. Het juiste antwoord was: {current_row['Capital']}")

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

# Reset optie
if st.sidebar.button("Reset Quiz & Score"):
    st.session_state.score = 0
    st.session_state.current_idx = None
    st.rerun()
