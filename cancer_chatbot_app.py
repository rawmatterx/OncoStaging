import streamlit as st
import fitz  # PyMuPDF
import docx
import re
from fpdf import FPDF
from tnm_staging import determine_tnm_stage

st.set_page_config(page_title="Cancer Staging Chatbot", layout="centered")
st.title("🤖 Cancer Staging Chatbot")
st.markdown("Upload your PET/CT report to get a staging summary and ask questions.")

uploaded_file = st.file_uploader("📤 Upload PET/CT Report (.pdf or .docx)", type=["pdf", "docx"])

def extract_text(file):
    if file.name.endswith(".pdf"):
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        return "\n".join([page.get_text() for page in pdf])
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    return ""

def extract_features(text):
    text = text.lower()
    features = {
        "cancer_type": "",
        "tumor_size_cm": 0,
        "lymph_nodes_involved": 0,
        "distant_metastasis": False,
        "liver_invasion": False,
        "tumor_depth": ""
    }
    if "gallbladder" in text:
        features["cancer_type"] = "gallbladder"
    elif "esophagus" in text:
        features["cancer_type"] = "esophageal"
    elif "breast" in text:
        features["cancer_type"] = "breast"
    elif "lung" in text:
        features["cancer_type"] = "lung"
    elif "colon" in text or "rectum" in text:
        features["cancer_type"] = "colorectal"
    elif "oral cavity" in text or "oropharynx" in text:
        features["cancer_type"] = "head and neck"

    size_match = re.search(r'(\d+(\.\d+)?)\s*(cm|mm)', text)
    if size_match:
        size_val = float(size_match.group(1))
        if "mm" in size_match.group(3):
            size_val /= 10
        features["tumor_size_cm"] = size_val

    features["lymph_nodes_involved"] = len(re.findall(r"lymph\s+node", text))
    features["distant_metastasis"] = "metastasis" in text or "metastases" in text
    features["liver_invasion"] = "liver invasion" in text or "involving segments" in text

    for keyword in ["mucosa", "submucosa", "muscularis", "subserosa", "serosa", "adventitia"]:
        if keyword in text:
            features["tumor_depth"] = keyword
            break
    return features

def generate_summary(stage, cancer_type):
    msg = f"Based on the report, this appears to be **{stage} {cancer_type.capitalize()} Cancer**.\n\n"
    if "IV" in stage:
        msg += "This indicates advanced disease with distant spread.\n"
    elif "III" in stage:
        msg += "This is a locally advanced stage.\n"
    elif "II" in stage:
        msg += "This is an early regional stage.\n"
    else:
        msg += "This appears to be an early stage disease.\n"
    msg += "\n⚠️ Please consult your oncologist before making any treatment decisions."
    return msg

def get_treatment_advice(cancer_type, stage):
    cancer_type = cancer_type.lower()
    stage = stage.upper()
    treatment_dict = {
        "gallbladder": {
            "I": "Surgical resection...",
            "II": "Extended cholecystectomy...",
            "III": "Surgical resection ± chemoradiotherapy...",
            "IV": "Systemic chemotherapy..."
        },
        "esophageal": {
            "I": "Endoscopic or surgical...",
            "II": "Neoadjuvant chemoradiotherapy...",
            "III": "Definitive chemoradiation...",
            "IV": "Systemic therapy..."
        },
        # Additional cancer types truncated for brevity
    }
    if stage.startswith("I"):
        stage_group = "I"
    elif "II" in stage:
        stage_group = "II"
    elif "III" in stage:
        stage_group = "III"
    elif "IV" in stage:
        stage_group = "IV"
    else:
        return "⚠️ Treatment info unavailable."
    return treatment_dict.get(cancer_type, {}).get(stage_group, "⚠️ No guideline available.")

def create_pdf(summary_text, filename="cancer_summary.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in summary_text.strip().split("\n"):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)
    return filename

if uploaded_file:
    with st.spinner("🔍 Analyzing report..."):
        text = extract_text(uploaded_file)
        features = extract_features(text)

        if features["cancer_type"]:
            staging = determine_tnm_stage(features["cancer_type"], features)
            st.success("✅ Report successfully analyzed.")
            st.subheader("🧠 Extracted Features")
            st.json(features)

            st.subheader("📊 TNM Staging Result")
            st.write(f"**T:** {staging['T']} | **N:** {staging['N']} | **M:** {staging['M']} | **Stage:** {staging['Stage']}")

            st.subheader("🤖 Ask the Chatbot")
            question = st.radio("Choose a question to ask:", [
                "🧾 What is my cancer stage?",
                "💊 What treatment is usually given?",
                "🧠 What does this mean in simple terms?",
                "📥 Download full summary"
            ])

            if st.button("Ask"):
                treatment = get_treatment_advice(features["cancer_type"], staging["Stage"])
                explanation = generate_summary(staging["Stage"], features["cancer_type"])
                summary_text = f"""Cancer Type: {features['cancer_type'].capitalize()}
Stage: {staging['Stage']}
TNM: T={staging['T']}, N={staging['N']}, M={staging['M']}

Explanation:
{explanation}

Treatment:
{treatment}

Disclaimer: This summary is AI-generated and not a substitute for clinical judgment.
"""
                if question == "🧾 What is my cancer stage?":
                    st.markdown(f"Your cancer is staged as **{staging['Stage']}**.")
                elif question == "💊 What treatment is usually given?":
                    st.markdown(treatment)
                elif question == "🧠 What does this mean in simple terms?":
                    st.markdown(explanation)
                elif question == "📥 Download full summary":
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button("📄 Download TXT", summary_text, file_name="cancer_summary.txt")
                    with col2:
                        pdf_path = create_pdf(summary_text)
                        with open(pdf_path, "rb") as f:
                            st.download_button("📄 Download PDF", f, file_name="cancer_summary.pdf")

                    st.radio("Was this summary helpful?", ["👍 Yes", "👎 No"])
        else:
            st.error("❌ Cancer type could not be identified from the report.")
