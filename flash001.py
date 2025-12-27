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
        # Mapping voor verschillende mogelijke kolomnamen
        df = df.rename(columns={'CountryName': 'Country', 'CapitalName': 'Capital', 
                                'country': 'Country', 'capital': 'Capital'})
        return df[['Country', 'Capital']].dropna().reset_index(drop=True)
    except Exception as e:
        st.error(f"Fout bij laden: {e}")
        return None

df = load_data()

# --- SESSIE BEHEER ---
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = random.randint(0, len(df) - 1)
if 'attempts' not in st.session_state:
    st.session_state.attempts = 0
if 'options' not in st.session_state:
    st.session_state.options = []
if 'feedback' not in st.session_state:
    st.session_state.feedback = None

def prepare_new_card():
    st.session_state.current_idx = random.randint(0, len(df) - 1)
    st.session_state.attempts = 0
    st.session_state.feedback = None
    
    # Genereer 4 opties (1 correct, 3 fout)
    correct_answer = df.iloc[st.session_state.current_idx]['Capital']
    wrong_answers = df[df['Capital'] != correct_answer]['Capital'].sample(3).tolist()
    
    options = wrong_answers + [correct_answer]
    random.shuffle(options)
    st.session_state.options = options

# Eerste keer opties genereren
if not st.session_state.options:
    prepare_new_card()

# --- UI ---
st.title("🌍 Capital Quiz Master")
st.sidebar.header("Je Prestaties")
st.sidebar.metric("Score", st.session_state.score)
st.sidebar.write(f"Pogingen voor huidige kaart: {st.session_state.attempts}/2")

if df is not None:
    current_country = df.iloc[st.session_state.current_idx]['Country']
    correct_capital = df.iloc[st.session_state.current_idx]['Capital']

    st.markdown(f"### Wat is de hoofdstad van **{current_country}**?")

    # Toon knoppen voor de 4 opties
    for option in st.session_state.options:
        if st.button(option, key=option, use_container_width=True):
            if option == correct_capital:
                st.session_state.feedback = ("success", f"Correct! Het is inderdaad {option}.")
                st.session_state.score += 1
                st.balloons()
            else:
                st.session_state.attempts += 1
                if st.session_state.attempts < 2:
                    st.session_state.feedback = ("warning", "Helaas, dat is niet juist. Probeer het nog één keer!")
                else:
                    st.session_state.feedback = ("error", f"Helaas, geen pogingen meer. Het juiste antwoord was: {correct_capital}")

    # Toon Feedback
    if st.session_state.feedback:
        type, msg = st.session_state.feedback
        if type == "success": st.success(msg)
        elif type == "warning": st.warning(msg)
        else: st.error(msg)

        # Toon "Volgende" knop als het antwoord goed is of pogingen op zijn
        if type == "success" or st.session_state.attempts >= 2:
            if st.button("Volgende Land ➡️"):
                prepare_new_card()
                st.rerun()

    if st.sidebar.button("Reset Score"):
        st.session_state.score = 0
        prepare_new_card()
        st.rerun()
