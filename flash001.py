import streamlit as st
import pandas as pd
import kagglehub
import os
import random

# --- DATA LADEN ---
@st.cache_data
def load_data():
    try:
        # Download de nieuwste versie
        path = kagglehub.dataset_download("nikitagrec/world-capitals-gps")
        
        # Zoek het CSV bestand
        files = [f for f in os.listdir(path) if f.endswith('.csv')]
        if not files:
            st.error("Geen CSV-bestand gevonden in de gedownloade map.")
            return None
            
        csv_path = os.path.join(path, files[0])
        df = pd.read_csv(csv_path)

        # DEBUG: Toon kolomnamen in de console als het misgaat
        # print(df.columns) 

        # We hernoemen de kolommen naar standaardnamen voor de app
        # De dataset gebruikt meestal 'CountryName' en 'CapitalName' of 'Country' en 'Capital'
        mapping = {
            'CountryName': 'Country',
            'CapitalName': 'Capital',
            'country': 'Country',
            'capital': 'Capital'
        }
        df = df.rename(columns=mapping)

        # Controleer of de benodigde kolommen nu bestaan
        if 'Country' in df.columns and 'Capital' in df.columns:
            return df[['Country', 'Capital']].dropna()
        else:
            st.error(f"Kolommen niet gevonden. Beschikbare kolommen: {list(df.columns)}")
            return None

    except Exception as e:
        st.error(f"Fout bij het laden van data: {e}")
        return None

df = load_data()

# --- SESSIE BEHEER ---
if 'current_index' not in st.session_state:
    st.session_state.current_index = random.randint(0, len(df) - 1)
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False

def next_card():
    st.session_state.current_index = random.randint(0, len(df) - 1)
    st.session_state.show_answer = False

# --- UI LAYOUT ---
st.set_page_config(page_title="Wereldsteden Flashcards", page_icon="🌍")
st.title("🌍 Hoofdsteden Flashcards")
st.write("Test je kennis van wereldsteden met deze dataset van Kaggle!")

if df is not None:
    row = df.iloc[st.session_state.current_index]
    
    # De Kaart (Card)
    st.markdown(f"""
        <div style="
            border: 2px solid #4CAF50;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            background-color: #f9f9f9;
            margin-bottom: 20px;">
            <h2 style="color: #333;">Wat is de hoofdstad van:</h2>
            <h1 style="color: #1E88E5;">{row['Country']}?</h1>
        </div>
    """, unsafe_allow_html=True)

    # Knoppen interactie
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Toon Antwoord", use_container_width=True):
            st.session_state.show_answer = True
            
    with col2:
        if st.button("Volgende Kaart ➡️", use_container_width=True):
            next_card()
            st.rerun()

    # Antwoord sectie
    if st.session_state.show_answer:
        st.markdown(f"""
            <div style="
                text-align: center;
                padding: 20px;
                background-color: #e3f2fd;
                border-radius: 10px;
                border: 1px dashed #1E88E5;">
                <h3 style="margin:0;">Het antwoord is:</h3>
                <h1 style="color: #D32F2F; margin:0;">{row['Capital']}</h1>
            </div>
        """, unsafe_allow_html=True)
        st.balloons()

else:
    st.error("Kon de dataset niet laden. Controleer je internetverbinding.")

# --- SIDEBAR INFO ---
st.sidebar.header("Statistieken")
st.sidebar.write(f"Totaal aantal landen in lijst: {len(df)}")
if st.sidebar.button("Reset Sessie"):
    next_card()
    st.rerun()
