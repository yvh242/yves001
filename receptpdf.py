import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import tempfile


# --------- PDF MAKER ---------
def maak_pdf_van_tekst(titel, volledige_tekst):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    doc = SimpleDocTemplate(
        tmp.name,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Titel", fontSize=20, spaceAfter=20))
    styles.add(ParagraphStyle(name="Body", fontSize=11, spaceAfter=10))

    story = []
    story.append(Paragraph(titel, styles["Titel"]))
    story.append(Spacer(1, 12))

    for alinea in volledige_tekst.split("\n\n"):
        story.append(Paragraph(alinea.replace("\n", "<br/>"), styles["Body"]))

    doc.build(story)
    return tmp.name


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

# Stap 1: combineer alles
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

# Stap 3: PDF
if st.button("📄 Genereer PDF"):
    if not titel or not volledige_tekst.strip():
        st.warning("Titel en tekst mogen niet leeg zijn.")
    else:
        pdf_pad = maak_pdf_van_tekst(titel, volledige_tekst)

        with open(pdf_pad, "rb") as f:
            st.download_button(
                "⬇️ Download PDF",
                f,
                file_name=f"{titel}.pdf",
                mime="application/pdf"
            )
