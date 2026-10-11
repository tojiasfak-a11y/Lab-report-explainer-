import re
import pdfplumber
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Lab Report Explainer", page_icon="🩺")

TAMIL = {
    "Hemoglobin": ("Hemoglobin kammiya irukku. Idhu ratha sogai (anemia) ku sign aagalam.", "Hemoglobin adhigama irukku."),
    "RBC Count": ("Sivappu anukkal kammiya irukku. Anemia-ku sign aagalam.", "Sivappu anukkal adhigama irukku."),
    "Hematocrit (PCV)": ("Rathathula sivappu anukkal alavu kammiya irukku.", "Rathathula sivappu anukkal alavu adhigama irukku."),
    "MCV": ("Sivappu anukkal size sirusa irukku. Iron kuraivaa irukkalam.", "Sivappu anukkal size periya irukku."),
    "Fasting Blood Sugar": ("Sugar alavu kammiya irukku.", "Sugar alavu konjam adhigama irukku. Doctor-a paarunga."),
    "Total Cholesterol": ("Cholesterol kammiya irukku.", "Cholesterol adhigama irukku. Unavu, udarpayirchi mukkiyam. Doctor-a paarunga."),
    "TSH": ("Thyroid hormone alavu kammiya irukku.", "Thyroid hormone alavu adhigama irukku."),
}
DEFAULT = ("Idhu pathi doctor-a kelunga.", "Idhu pathi doctor-a kelunga.")

P1 = r"^([A-Za-z() ]+?)\s+([\d.]+)\s+(\S+)\s+([\d.]+)\s*-\s*([\d.]+)$"
P2 = r"^([A-Za-z() ]+?)\s+([\d.]+)\s+(\S+)\s+Below\s+([\d.]+)$"


def analyze(file):
    with pdfplumber.open(file) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    lines = text.split("\n")
    rows = [m.groups() for l in lines if (m := re.match(P1, l))]
    rows += [(m[1], m[2], m[3], "0", m[4]) for l in lines if (m := re.match(P2, l))]
    df = pd.DataFrame(rows, columns=["Test", "Value", "Unit", "Low", "High"])
    if df.empty:
        return df
    df[["Value", "Low", "High"]] = df[["Value", "Low", "High"]].astype(float)
    df["Status"] = df.apply(
        lambda r: "LOW" if r.Value < r.Low else ("HIGH" if r.Value > r.High else "NORMAL"),
        axis=1,
    )
    df["Explanation"] = df.apply(
        lambda r: "Normal-a irukku." if r.Status == "NORMAL"
        else TAMIL.get(r.Test, DEFAULT)[0 if r.Status == "LOW" else 1],
        axis=1,
    )
    return df


st.title("🩺 Lab Report Explainer")
st.write("Blood report PDF upload pannunga. Ovvoru value-um enna artham nu Tamil-la explain pannuvom.")
st.warning("Idhu doctor advice illa. Dhayavu seidhu doctor-a paarunga. Chest pain, moochu thinaral mathiri emergency irundha udane doctor-a paarunga.")

uploaded = st.file_uploader("Report PDF (digital PDF mattum)", type="pdf")

if uploaded:
    df = analyze(uploaded)
    if df.empty:
        st.error("Intha PDF-la tests-a padikka mudiyala. Digital (text select panna mudiyura) PDF upload pannunga.")
    else:
        abnormal = df[df.Status != "NORMAL"]
        st.subheader(f"Summary: {len(abnormal)} value(s) normal-a illa")
        for _, r in df.iterrows():
            line = f"**{r.Test}**: {r.Value:g} {r.Unit} (normal: {r.Low:g} - {r.High:g}) → **{r.Status}**\n\n{r.Explanation}"
            if r.Status == "NORMAL":
                st.success(line)
            else:
                st.error(line)
        with st.expander("Full table paarunga"):
            st.dataframe(df[["Test", "Value", "Unit", "Low", "High", "Status"]])
        st.caption("Ungal report engayum save aagaadhu.")
