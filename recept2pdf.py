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

st.subheader("2. Vrije Layout & Posities Instellen")
uploaded_file = st.file_uploader("Voeg een foto toe (optioneel)", type=["jpg", "jpeg", "png"])

# Vrije keuze voor de positie van elk blok
col_l1, col_l2, col_l3 = st.columns(3)
with col_l1:
    layout_ingr = st.selectbox("Positie Ingrediënten", ["Links", "Rechts", "Onder elkaar"], index=0)
with col_l2:
    layout_bereiding = st.selectbox("Positie Bereiding", ["Onder alles", "Naast Ingrediënten", "Volledig vrij"], index=0)
with col_l3:
    layout_foto = st.selectbox("Positie Foto", ["Rechts", "Links", "Bovenin"], index=0)

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.markdown("### 📏 Foto Afmetingen")
    img_width = st.slider("Breedte foto (mm)", 10, 150, 60)
    img_height = st.slider("Hoogte foto (mm)", 10, 150, 60)
with col2:
    st.markdown("### ✍️ Tekstgrootte")
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
    
    # Hulpfuncties voor blokken
    def draw_ingrediënten(x=10, y=None, w=90):
        if y is not None:
            pdf.set_xy(x, y)
        else:
            pdf.set_x(x)
        pdf.set_font("Arial", 'B', size_body + 2)
        pdf.cell(w, 8, "Ingrediënten:", ln=True)
        pdf.set_font("Arial", '', size_body)
        for line in ingr_input.split('\n'):
            if line.strip():
                pdf.set_x(x)
                pdf.cell(w, 5, safe_text(f"- {line.strip()}"), ln=True)

    def draw_foto(x, y):
        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                img = Image.open(uploaded_file)
                img.save(tmp_file.name)
                pdf.image(tmp_file.name, x=x, y=y, w=img_width, h=img_height)
                os.unlink(tmp_file.name)

    def draw_bereiding(y_pos=None):
        if y_pos is not None:
            pdf.set_y(y_pos)
        pdf.ln(5)
        pdf.set_font("Arial", 'B', size_body + 2)
        pdf.cell(0, 8, "Bereidingswijze:", ln=True)
        pdf.set_font("Arial", '', size_body)
        pdf.multi_cell(0, 5, safe_text(bereiding_input))

    # Logica op basis van gekozen posities
    # Scenario A: Ingrediënten Links, Foto Rechts (Standaard side-by-side)
    if layout_ingr == "Links" and layout_foto == "Rechts" and uploaded_file:
        draw_ingrediënten(x=10, y=start_y, w=95)
        draw_foto(x=110, y=start_y)
        
        ingr_bottom = pdf.get_y()
        foto_bottom = start_y + img_height
        next_y = max(ingr_bottom, foto_bottom) + 10
        
        if layout_bereiding == "Onder alles":
            draw_bereiding(y_pos=next_y)

    # Scenario B: Foto Links, Ingrediënten Rechts
    elif layout_foto == "Links" and layout_ingr == "Rechts" and uploaded_file:
        draw_foto(x=10, y=start_y)
        draw_ingrediënten(x=80, y=start_y, w=120)
        
        ingr_bottom = pdf.get_y()
        foto_bottom = start_y + img_height
        next_y = max(ingr_bottom, foto_bottom) + 10
        
        if layout_bereiding == "Onder alles":
            draw_bereiding(y_pos=next_y)

    # Scenario C: Alles onder elkaar (of als geen foto is ingevoerd)
    else:
        current_y = start_y
        if uploaded_file and layout_foto == "Bovenin":
            draw_foto(x=10, y=current_y)
            current_y += img_height + 10
            
        draw_ingrediënten(x=10, y=current_y, w=180)
        current_y = pdf.get_y() + 10
        
        if uploaded_file and layout_foto == "Rechts":
            # Foto kan hiernaast of onder gezet worden
            pass
            
        draw_bereiding(y_pos=current_y)

    pdf_output = pdf.output()
    
    st.download_button(
        label="Download PDF Bestand",
        data=bytes(pdf_output),
        file_name=f"{safe_text(titel_input).replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
