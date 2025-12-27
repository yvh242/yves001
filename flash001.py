import streamlit as st
import pandas as pd
import kagglehub
import os
import random

# --- DATA LADEN ---
@st.cache_data
def load_data():
    # Download dataset
    path = kagglehub.dataset_download("nikitagrec/world-capitals-gps")
    
    # Zoek naar het CSV bestand in de gedownloade map
    for file in os.listdir(path):
        if file.endswith(".csv"):
            csv_path = os.path.join(path, file)
            df = pd.read_csv(csv_path)
            # Opschonen: we hebben alleen Land en Hoofdstad nodig
            return df[['CountryName', 'CapitalName']].dropna()
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
            <h1 style="color: #1E88E5;">{row['CountryName']}?</h1>
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
                <h1 style="color: #D32F2F; margin:0;">{row['CapitalName']}</h1>
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
