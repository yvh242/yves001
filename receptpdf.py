import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import re
import tempfile


# --------- TEKST PARSER ---------
def structureer_recept(vrije_tekst):
    ingred = []
    stappen = []

    tekst = vrije_tekst.lower()

    # splits op ingrediënten / bereiding
    if "bereiding" in tekst:
        delen = re.split(r"bereiding[:\-]?", vrije_tekst, flags=re.IGNORECASE)
        ingred_tekst = delen[0]
        bereiding_tekst = delen[1]
    else:
        ingred_tekst = vrije_tekst
        bereiding_tekst = ""

    # ingrediënten herkennen
    for lijn in ingred_tekst.split(","):
        lijn = lijn.strip()
        if len(lijn) > 2:
            ingred.append(lijn.capitalize())

    # stappen herkennen
    for zin in re.split(r"\.|\\n", bereiding_tekst):
        zin = zin.strip()
        if len(zin) > 5:
            stappen.append(zin.capitalize())

    return ingred, stappen


# --------- PDF MAKER ---------
def maak_pdf(titel, ingredienten, stappen):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    doc = SimpleDocTemplate(
        tmp.name,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Titel", fontSize=20, spaceAfter=20))
    styles.add(ParagraphStyle(name="Kop", fontSize=14, spaceBefore=12, spaceAfter=8))

    story = []
    story.append(Paragraph(titel, styles["Titel"]))

    story.append(Paragraph("Ingrediënten", styles["Kop"]))
    story.append(ListFlowable(
        [ListItem(Paragraph(i, styles["Normal"])) for i in ingredienten],
        bulletType="bullet"
    ))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Bereidingswijze", styles["Kop"]))
    story.append(ListFlowable(
        [ListItem(Paragraph(s, styles["Normal"])) for s in stappen],
        bulletType="1"
    ))

    doc.build(story)
    return tmp.name


# --------- STREAMLIT UI ---------
st.title("🍽️ Recept → PDF")

titel = st.text_input("Recept titel")

vrije_tekst = st.text_area(
    "Plak hier je volledige recept (vrije tekst)",
    height=200,
    placeholder="Ingrediënten: ... Bereiding: ..."
)

if st.button("✨ Structureer recept"):
    ingredienten, stappen = structureer_recept(vrije_tekst)

    st.subheader("Ingrediënten")
    for i in ingredienten:
        st.write("•", i)

    st.subheader("Bereidingswijze")
    for idx, s in enumerate(stappen, 1):
        st.write(f"{idx}. {s}")

    if st.button("📄 Download PDF"):
        pdf_pad = maak_pdf(titel, ingredienten, stappen)
        with open(pdf_pad, "rb") as f:
            st.download_button(
                "⬇️ Download recept PDF",
                f,
                file_name=f"{titel}.pdf",
                mime="application/pdf"
            )
