import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import tempfile


# --------- PDF MAKER ---------
def maak_pdf(titel, ingredienten, stappen):
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
    styles.add(ParagraphStyle(name="Kop", fontSize=14, spaceBefore=12, spaceAfter=8))

    story = []

    # Titel
    story.append(Paragraph(titel, styles["Titel"]))
    story.append(Spacer(1, 12))

    # Ingrediënten
    story.append(Paragraph("Ingrediënten", styles["Kop"]))
    story.append(
        ListFlowable(
            [ListItem(Paragraph(i, styles["Normal"])) for i in ingredienten],
            bulletType="bullet"
        )
    )

    story.append(Spacer(1, 12))

    # Bereidingswijze
    story.append(Paragraph("Bereidingswijze", styles["Kop"]))
    story.append(
        ListFlowable(
            [ListItem(Paragraph(s, styles["Normal"])) for s in stappen],
            bulletType="1"
        )
    )

    doc.build(story)
    return tmp.name


# --------- STREAMLIT UI ---------
st.set_page_config(page_title="Recept → PDF", page_icon="🍽️")
st.title("🍽️ Recept → PDF")

titel = st.text_input("Titel van het recept")

ingredienten_tekst = st.text_area(
    "Ingrediënten (1 per lijn)",
    height=150,
    placeholder="6 stronken witloof\n6 sneden ham\n200 g kaas"
)

bereiding_tekst = st.text_area(
    "Bereidingswijze (1 stap per lijn)",
    height=200,
    placeholder="Kook het witloof beetgaar\nRol in ham\nMaak de kaassaus\nBak 30 minuten"
)

# Verwerking
ingredienten = [i.strip() for i in ingredienten_tekst.split("\n") if i.strip()]
stappen = [s.strip() for s in bereiding_tekst.split("\n") if s.strip()]

if st.button("📄 Genereer PDF"):
    if not titel or not ingredienten or not stappen:
        st.warning("Vul titel, ingrediënten en bereidingswijze in.")
    else:
        pdf_pad = maak_pdf(titel, ingredienten, stappen)

        with open(pdf_pad, "rb") as f:
            st.download_button(
                label="⬇️ Download PDF",
                data=f,
                file_name=f"{titel}.pdf",
                mime="application/pdf"
            )
