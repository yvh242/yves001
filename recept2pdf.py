import streamlit as st
from fpdf import FPDF
from PIL import Image
import tempfile
import os

# --- PDF GENERATOR KLASSE ---
class RecipePDF(FPDF):
    def header(self):
        pass

# Functie om speciale tekens om te zetten zodat de standaard Arial-font niet crasht
def safe_text(text):
    if not text:
        return ""
    return text.encode('latin-1', 'replace').decode('latin-1')

# --- APP LAYOUT ---
st.set_page_config(page_title="Recept naar PDF Maker", layout="centered")
st.title("🍳 Recept naar PDF Generator")

st.subheader("1. Voer je recept in")

titel_input = st.text_input("Titel van het recept", "Heerlijke Pasta")
ingr_input = st.text_area("Ingrediënten (één per regel)", "500g Pasta\n2 teentjes knoflook\nOlijfolie", height=150)
bereiding_input = st.text_area("Bereidingswijze", "Kook de pasta al dente en meng met de overige ingrediënten.", height=200)

st.divider()

st.subheader("2. Foto & Tekst Instellingen")
uploaded_file = st.file_uploader("Voeg een foto toe (optioneel)", type=["jpg", "jpeg", "png"])

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📏 Foto Afmetingen")
    img_width = st.slider("Breedte foto (mm)", 10, 150, 60)
    img_height = st.slider("Hoogte foto (mm)", 10, 150, 60)

with col2:
    st.markdown("### ✍️ Tekstgrootte")
    size_titel = st.slider("Grootte Titel", 12, 40, 24)
    size_body = st.slider("Grootte Inhoud", 8, 20, 11)

# --- PDF GENERATIE LOGICA ---
if st.button("Genereer en Download PDF"):
    pdf = RecipePDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', size_titel)
    
    # Titel
    pdf.cell(0, 15, safe_text(titel_input), ln=True)
    pdf.ln(5)
    
    start_y = pdf.get_y()
    
    # Ingrediënten (Links)
    pdf.set_font("Arial", 'B', size_body + 2)
    pdf.cell(100, 10, "Ingrediënten:", ln=True)
    pdf.set_font("Arial", '', size_body)
    
    for line in ingr_input.split('\n'):
        if line.strip():
            pdf.cell(100, 6, safe_text(f"- {line.strip()}"), ln=True)
    
    # Foto (Rechts van de ingrediënten plaatsen)
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            img = Image.open(uploaded_file)
            img.save(tmp_file.name)
            pdf.image(tmp_file.name, x=110, y=start_y, w=img_width, h=img_height)
            os.unlink(tmp_file.name)

    # Bereidingswijze
    current_y = pdf.get_y()
    photo_bottom_y = start_y + img_height if uploaded_file else 0
    new_y = max(current_y, photo_bottom_y) + 10
    
    pdf.set_y(new_y)
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
