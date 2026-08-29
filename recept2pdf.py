import streamlit as st
from fpdf import FPDF
from PIL import Image
import tempfile
import os

class RecipePDF(FPDF):
    def header(self):
        pass

def safe_text(text):
    if not text:
        return ""
    return text.encode('latin-1', 'replace').decode('latin-1')

st.set_page_config(page_title="Recept naar PDF Maker", layout="centered")
st.title("🍳 Recept naar PDF Generator")

st.subheader("1. Voer je recept in")
titel_input = st.text_input("Titel van het recept", "Heerlijke Pasta")
ingr_input = st.text_area("Ingrediënten (één per regel)", "500g Pasta\n2 teentjes knoflook\nOlijfolie", height=150)
bereiding_input = st.text_area("Bereidingswijze", "Kook de pasta al dente en meng met de overige ingrediënten.", height=200)

st.divider()

st.subheader("2. Foto & Instellingen")
uploaded_file = st.file_uploader("Voeg een foto toe (optioneel)", type=["jpg", "jpeg", "png"])

# Keuze voor de opmaak / volgorde van de blokken
layout_keuze = st.selectbox(
    "Kies de indeling op de PDF",
    [
        "Standaard: Ingrediënten links, Foto rechts, Bereidingswijze onder",
        "Omgekeerd: Foto links, Ingrediënten rechts, Bereidingswijze onder",
        "Volledig onder elkaar: Foto bovenaan, Ingrediënten, Bereidingswijze"
    ]
)

col1, col2 = st.columns(2)
with col1:
    img_width = st.slider("Breedte foto (mm)", 10, 150, 60)
    img_height = st.slider("Hoogte foto (mm)", 10, 150, 60)
with col2:
    size_titel = st.slider("Grootte Titel", 12, 40, 24)
    size_body = st.slider("Grootte Inhoud", 8, 20, 11)

if st.button("Genereer en Download PDF"):
    pdf = RecipePDF()
    pdf.add_page()
    
    # Titel
    pdf.set_font("Arial", 'B', size_titel)
    pdf.cell(0, 15, safe_text(titel_input), ln=True)
    pdf.ln(5)
    
    start_y = pdf.get_y()
    
    # Hulpfunctie om ingrediënten blok te schrijven
    def write_ingrediënten(x_pos=None, y_pos=None, max_w=0):
        if x_pos is not None and y_pos is not None:
            pdf.set_xy(x_pos, y_pos)
        pdf.set_font("Arial", 'B', size_body + 2)
        pdf.cell(max_w, 10, "Ingrediënten:", ln=True)
        pdf.set_font("Arial", '', size_body)
        for line in ingr_input.split('\n'):
            if line.strip():
                if x_pos is not None:
                    pdf.set_x(x_pos)
                pdf.cell(max_w, 6, safe_text(f"- {line.strip()}"), ln=True)

    # Hulpfunctie om foto te plaatsen
    def write_foto(x_pos, y_pos):
        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                img = Image.open(uploaded_file)
                img.save(tmp_file.name)
                pdf.image(tmp_file.name, x=x_pos, y=y_pos, w=img_width, h=img_height)
                os.unlink(tmp_file.name)

    bottom_blocks_y = start_y

    if "Standaard" in layout_keuze:
        # Ingrediënten links (breedte 100mm), Foto rechts op x=110
        write_ingrediënten(max_w=100)
        if uploaded_file:
            write_foto(x_pos=110, y_pos=start_y)
        
        current_y = pdf.get_y()
        photo_bottom_y = start_y + img_height if uploaded_file else 0
        bottom_blocks_y = max(current_y, photo_bottom_y) + 10

    elif "Omgekeerd" in layout_keuze:
        # Foto links op x=10, Ingrediënten rechts op x=80
        if uploaded_file:
            write_foto(x_pos=10, y_pos=start_y)
        
        write_ingrediënten(x_pos=80, y_pos=start_y, max_w=120)
        
        current_y = pdf.get_y()
        photo_bottom_y = start_y + img_height if uploaded_file else 0
        bottom_blocks_y = max(current_y, photo_bottom_y) + 10

    else:
        # Volledig onder elkaar: Foto eerst (centraal of links), dan ingrediënten
        if uploaded_file:
            write_foto(x_pos=10, y_pos=start_y)
            bottom_blocks_y = start_y + img_height + 10
        
        write_ingrediënten(y_pos=bottom_blocks_y if uploaded_file else start_y)
        bottom_blocks_y = pdf.get_y() + 10

    # Bereidingswijze komt altijd onderaan de gekozen bovenste blokken
    pdf.set_y(bottom_blocks_y)
    pdf.set_font("Arial", 'B', size_body + 2)
    pdf.cell(0, 10, "Bereidingswijze:", ln=True)
    pdf.set_font("Arial", '', size_body)
    pdf.multi_cell(0, 6, safe_text(bereiding_input))
    
    pdf_output = pdf.output()
    
    st.download_button(
        label="Download PDF Bestand",
        data=bytes(pdf_output),
        file_name=f"{safe_text(titel_input).replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
