import streamlit as st
from fpdf import FPDF
from PIL import Image
import tempfile
import os

# --- PDF GENERATOR KLASSE ---
class RecipePDF(FPDF):
    def header(self):
        self.set_font("Arial", 'B', 15)
        self.cell(0, 10, "", ln=True, align='C')
        self.ln(5)

# --- APP LAYOUT ---
st.set_page_config(page_title="Recept naar PDF Maker", layout="wide")
st.title("🍳 Recept naar PDF Generator")

# Kolommen voor input
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Voer de gegevens in")
    titel_input = st.text_input("Titel van het recept", "Heerlijke Pasta")
    ingr_input = st.text_area("Ingrediënten (één per regel)", "500g Pasta\n2 teentjes knoflook\nOlijfolie")
    bereiding_input = st.text_area("Bereidingswijze", "Kook de pasta al dente...")
    
    uploaded_file = st.file_uploader("Voeg een foto toe (optioneel)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        st.subheader("📷 Foto Instellingen")
        img_width = st.slider("Breedte foto (mm)", 10, 100, 50)
        img_height = st.slider("Hoogte foto (mm)", 10, 100, 50)

with col2:
    st.subheader("2. Controleer & Pas aan")
    # Bewerkbare tekstvelden voor de eindstructuur
    final_titel = st.text_input("Titel aanpassen", titel_input)
    final_ingr = st.text_area("Ingrediënten aanpassen", ingr_input, height=150)
    final_bereiding = st.text_area("Bereidingswijze aanpassen", bereiding_input, height=150)

# --- PDF GENERATIE LOGICA ---
if st.button("Genereer PDF"):
    pdf = RecipePDF()
    pdf.add_page()
    
    # Titel
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, final_titel, ln=True)
    pdf.ln(10)
    
    # Startpunt voor Ingrediënten
    start_y = pdf.get_y()
    
    # Ingrediënten (Links)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, "Ingrediënten:", ln=True)
    pdf.set_font("Arial", '', 11)
    for line in final_ingr.split('\n'):
        pdf.cell(100, 6, f"- {line}", ln=True)
    
    # Foto (Rechts van de ingrediënten)
    if uploaded_file:
        # Sla foto tijdelijk op voor de PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            img = Image.open(uploaded_file)
            img.save(tmp_file.name)
            # Plaats foto rechts (x=120) op de hoogte van de ingrediënten
            pdf.image(tmp_file.name, x=120, y=start_y, w=img_width, h=img_height)
            os.unlink(tmp_file.name) # Verwijder tijdelijk bestand

    # Bereidingswijze (Onder de ingrediënten/foto)
    # Bepaal de nieuwe Y positie zodat tekst niet over foto heen gaat
    current_y = max(pdf.get_y(), start_y + (img_height if uploaded_file else 0))
    pdf.set_y(current_y + 10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Bereidingswijze:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 6, final_bereiding)
    
    # PDF Output
    pdf_output = pdf.output()
    st.download_button(
        label="Download Recept PDF",
        data=bytes(pdf_output),
        file_name=f"{final_titel.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
    st.success("PDF is klaar om te downloaden!")
