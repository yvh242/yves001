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

st.set_page_config(page_title="Recept naar PDF Maker", layout="wide")
st.title("🍳 Recept naar PDF Generator - Vrije Posities & Formaten")

# --- RECEPT DATA ---
col_in1, col_in2 = st.columns(2)
with col_in1:
    titel_input = st.text_input("Titel van het recept", "Heerlijke Pasta")
    ingr_input = st.text_area("Ingrediënten (één per regel)", "500g Pasta\n2 teentjes knoflook\nOlijfolie", height=120)
with col_in2:
    bereiding_input = st.text_area("Bereidingswijze", "Kook de pasta al dente en meng met de overige ingrediënten.", height=190)
    uploaded_file = st.file_uploader("Voeg een foto toe (optioneel)", type=["jpg", "jpeg", "png"])

st.divider()

# --- LAYOUT CONTROLEPANEEL (X, Y, W, H) ---
st.subheader("🎛️ Blok Instellingen (Positie & Grootte in mm)")
st.caption("A4 formaat is ca. 210 mm breed en 297 mm hoog.")

tab_titel, tab_ingr, tab_bereiding, tab_foto = st.tabs(["Titel", "Ingrediënten", "Bereidingswijze", "Foto"])

with tab_titel:
    c1, c2, c3 = st.columns(3)
    t_x = c1.slider("Titel X-positie", 0, 150, 10, key="tx")
    t_y = c2.slider("Titel Y-positie", 0, 280, 10, key="ty")
    t_size = c3.slider("Titel Tekstgrootte", 10, 40, 24, key="tsz")

with tab_ingr:
    c1, c2, c3, c4 = st.columns(4)
    i_x = c1.slider("Ingr. X-positie", 0, 200, 10, key="ix")
    i_y = c2.slider("Ingr. Y-positie", 0, 280, 40, key="iy")
    i_w = c3.slider("Ingr. Breedte", 20, 190, 90, key="iw")
    i_size = c4.slider("Ingr. Tekstgrootte", 8, 20, 11, key="isz")

with tab_bereiding:
    c1, c2, c3, c4 = st.columns(4)
    b_x = c1.slider("Bereid. X-positie", 0, 200, 10, key="bx")
    b_y = c2.slider("Bereid. Y-positie", 0, 280, 130, key="by")
    b_w = c3.slider("Bereid. Breedte", 50, 190, 190, key="bw")
    b_size = c4.slider("Bereid. Tekstgrootte", 8, 20, 11, key="bsz")

with tab_foto:
    c1, c2, c3, c4 = st.columns(4)
    f_x = c1.slider("Foto X-positie", 0, 200, 110, key="fx")
    f_y = c2.slider("Foto Y-positie", 0, 280, 40, key="fy")
    f_w = c3.slider("Foto Breedte (mm)", 10, 150, 80, key="fw")
    f_h = c4.slider("Foto Hoogte (mm)", 10, 150, 60, key="fh")

st.divider()

# --- PDF GENERATIE ---
if st.button("Genereer en Download PDF", type="primary"):
    pdf = RecipePDF()
    pdf.add_page()
    
    # 1. Titel tekenen
    pdf.set_xy(t_x, t_y)
    pdf.set_font("Arial", 'B', t_size)
    pdf.cell(0, 15, safe_text(titel_input), ln=True)
    
    # 2. Ingrediënten tekenen
    pdf.set_xy(i_x, i_y)
    pdf.set_font("Arial", 'B', i_size + 2)
    pdf.cell(i_w, 8, "Ingrediënten:", ln=True)
    pdf.set_font("Arial", '', i_size)
    for line in ingr_input.split('\n'):
        if line.strip():
            pdf.set_x(i_x)
            pdf.cell(i_w, 5, safe_text(f"- {line.strip()}"), ln=True)
            
    # 3. Bereidingswijze tekenen
    pdf.set_xy(b_x, b_y)
    pdf.set_font("Arial", 'B', b_size + 2)
    pdf.cell(b_w, 8, "Bereidingswijze:", ln=True)
    pdf.set_font("Arial", '', b_size)
    pdf.set_x(b_x)
    pdf.multi_cell(b_w, 5, safe_text(bereiding_input))
    
    # 4. Foto tekenen (indien geüpload)
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            img = Image.open(uploaded_file)
            img.save(tmp_file.name)
            pdf.image(tmp_file.name, x=f_x, y=f_y, w=f_w, h=f_h)
            os.unlink(tmp_file.name)
            
    pdf_output = pdf.output()
    
    st.download_button(
        label="Download PDF Bestand",
        data=bytes(pdf_output),
        file_name=f"{safe_text(titel_input).replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
