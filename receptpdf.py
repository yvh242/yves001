import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import tempfile
from PIL import Image as PILImage


# --------- PDF MAKER ---------
def maak_pdf(titel, ingredienten, bereiding, foto_pad=None,
             foto_breedte_cm=8, foto_hoogte_cm=6):

    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    doc = SimpleDocTemplate(
        tmp_pdf.name,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Titel", fontSize=20, spaceAfter=20))
    styles.add(ParagraphStyle(name="Kop", fontSize=14, spaceAfter=10))
    styles.add(ParagraphStyle(name="Body", fontSize=11, spaceAfter=6))

    story = []

    # Titel
    story.append(Paragraph(titel, styles["Titel"]))

    # Ingrediënten tekst
    ingredienten_par = Paragraph(
        "<b>Ingrediënten</b><br/>" +
        ingredienten.replace("\n", "<br/>"),
        styles["Body"]
    )

    # Foto (optioneel)
    foto_obj = ""
    if foto_pad:
        foto_obj = Image(
            foto_pad,
            width=foto_breedte_cm * cm,
            height=foto_hoogte_cm * cm
        )

    # Tabel: ingrediënten links, foto rechts
    tabel = Table(
        [[ingredienten_par, foto_obj]],
        colWidths=[9 * cm, 7 * cm]
    )

    tabel.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    story.append(tabel)
    story.append(Spacer(1, 20))

    # Bereiding
    story.append(Paragraph("Bereidingswijze", styles["Kop"]))
    for stap in bereiding.split("\n"):
        story.append(Paragraph(stap, styles["Body"]))

    doc.build(story)
    return tmp_pdf.name


# --------- STREAMLIT UI ---------
st.set_page_config(page_title="Recept → PDF", page_icon="🍽️")
st.title("🍽️ Recept → PDF")

titel = st.text_input("Titel van het recept")

ingredienten = st.text_area(
    "Ingrediënten (1 per lijn)",
    height=120
)

bereiding = st.text_area(
    "Bereidingswijze (1 stap per lijn)",
    height=150
)

foto = st.file_uploader(
    "📷 Optionele foto van het gerecht",
    type=["jpg", "jpeg", "png"]
)

col1, col2 = st.columns(2)
with col1:
    foto_breedte_cm = st.number_input(
        "Foto breedte (cm)",
        min_value=3.0,
        max_value=15.0,
        value=8.0,
        step=0.5
    )

with col2:
    foto_hoogte_cm = st.number_input(
        "Foto hoogte (cm)",
        min_value=3.0,
        max_value=15.0,
        value=6.0,
        step=0.5
    )

# Foto tijdelijk opslaan
foto_pad = None
if foto:
    tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    img = PILImage.open(foto)
    img.save(tmp_img.name)
    foto_pad = tmp_img.name
    st.image(img, caption="Geselecteerde foto", use_container_width=True)

# Stap 1: combineer tekst
if st.button("📝 Maak voorbeeldtekst"):
    gecombineerde_tekst = f"""INGREDIËNTEN
{ingredienten}

BEREIDINGSWIJZE
{bereiding}
"""
    st.session_state["volledige_tekst"] = gecombineerde_tekst

# Stap 2: bewerkbare totaaltekst
volledige_tekst = st.text_area(
    "Volledige tekst (vrij bewerkbaar)",
    height=300,
    value=st.session_state.get("volledige_tekst", "")
)

# Stap 3: PDF genereren
if st.button("📄 Genereer PDF"):
    if not titel:
        st.warning("Titel is verplicht.")
    else:
        pdf_pad = maak_pdf(
            titel,
            ingredienten,
            bereiding,
            foto_pad,
            foto_breedte_cm,
            foto_hoogte_cm
        )

        with open(pdf_pad, "rb") as f:
            st.download_button(
                "⬇️ Download PDF",
                f,
                file_name=f"{titel}.pdf",
                mime="application/pdf"
            )
