import streamlit as st
import fitz  # PyMuPDF
import docx
import re
import os

DOWNLOAD_COUNTER_FILE = "download_count.txt"

def get_download_count():
    if os.path.exists(DOWNLOAD_COUNTER_FILE):
        with open(DOWNLOAD_COUNTER_FILE, "r") as f:
            return int(f.read().strip())
    return 0

def increment_download_count():
    count = get_download_count() + 1
    with open(DOWNLOAD_COUNTER_FILE, "w") as f:
        f.write(str(count))

from tnm_staging import determine_tnm_stage

st.set_page_config(page_title="Cancer Staging Chatbot", layout="centered")
st.title("🤖 Cancer Staging Chatbot")
st.markdown("Upload your PET/CT report to get a staging summary and ask questions.")

# ------------------- File Upload ------------------- #
uploaded_file = st.file_uploader("📤 Upload PET/CT Report (.pdf or .docx)", type=["pdf", "docx"])

def extract_text(file):
    if file.name.endswith(".pdf"):
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        return "\n".join([page.get_text() for page in pdf])
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    return ""

# ------------------- Feature Extraction ------------------- #
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

# ------------------- Explanation Generator ------------------- #
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

# ------------------- Treatment Suggestion ------------------- #
def get_treatment_advice(cancer_type, stage):
    cancer_type = cancer_type.lower()
    stage = stage.upper()

    treatment_dict = {
        "gallbladder": {
            "I": "Surgical resection (simple cholecystectomy or wedge resection of liver segments IVB and V).\n🔗 NCCN Gallbladder Guidelines: https://www.nccn.org/professionals/physician_gls/pdf/hepatobiliary.pdf",
            "II": "Extended cholecystectomy with lymph node dissection.\n🔗 NCCN Gallbladder Guidelines",
            "III": "Surgical resection ± adjuvant chemoradiotherapy (e.g., capecitabine).\n🔗 NCCN Gallbladder Guidelines",
            "IV": "Systemic chemotherapy (e.g., gemcitabine + cisplatin). Consider palliative care.\n🔗 NCCN Gallbladder Guidelines"
        },
        "esophageal": {
            "I": "Endoscopic mucosal resection or esophagectomy.\n🔗 NCCN Esophageal Guidelines: https://www.nccn.org/professionals/physician_gls/pdf/esophageal.pdf",
            "II": "Neoadjuvant chemoradiotherapy followed by surgery.\n🔗 NCCN Esophageal Guidelines",
            "III": "Definitive chemoradiation or surgery after neoadjuvant therapy.\n🔗 NCCN Esophageal Guidelines",
            "IV": "Systemic therapy or palliative RT/stent placement.\n🔗 NCCN Esophageal Guidelines"
        },
        "breast": {
            "I": "Surgery (BCS or mastectomy) ± adjuvant RT.\n🔗 NCCN Breast Guidelines: https://www.nccn.org/professionals/physician_gls/pdf/breast.pdf",
            "II": "Surgery + chemo/hormonal therapy + radiation.\n🔗 NCCN Breast Guidelines",
            "III": "Neoadjuvant chemotherapy → surgery + adjuvant therapy.\n🔗 NCCN Breast Guidelines",
            "IV": "Systemic therapy (chemo, endocrine, HER2-targeted) based on biomarkers.\n🔗 NCCN Breast Guidelines"
        },
        "lung": {
            "I": "Surgical resection ± adjuvant chemo.\n🔗 NCCN NSCLC Guidelines: https://www.nccn.org/professionals/physician_gls/pdf/nscl.pdf",
            "II": "Surgery + chemo ± radiation.\n🔗 NCCN NSCLC Guidelines",
            "III": "Concurrent chemoradiotherapy ± immunotherapy (durvalumab).\n🔗 NCCN NSCLC Guidelines",
            "IV": "Targeted therapy, immunotherapy, or chemo based on mutations.\n🔗 NCCN NSCLC Guidelines"
        },
        "colorectal": {
            "I": "Surgical resection (segmental colectomy).\n🔗 NCCN Colon Guidelines: https://www.nccn.org/professionals/physician_gls/pdf/colon.pdf",
            "II": "Surgery ± adjuvant chemo (if high-risk).\n🔗 NCCN Colon Guidelines",
            "III": "Surgery + adjuvant FOLFOX or CAPOX.\n🔗 NCCN Colon Guidelines",
            "IV": "Systemic therapy ± targeted therapy. Resect mets if operable.\n🔗 NCCN Colon Guidelines"
        },
        "head and neck": {
            "I": "Surgery or radiation alone.\n🔗 NCCN Head & Neck Guidelines: https://www.nccn.org/professionals/physician_gls/pdf/head-and-neck.pdf",
            "II": "Surgery ± adjuvant RT.\n🔗 NCCN Head & Neck Guidelines",
            "III": "Surgery + RT/chemo or concurrent chemoradiation.\n🔗 NCCN Head & Neck Guidelines",
            "IV": "Systemic therapy ± RT. Consider immunotherapy (nivolumab).\n🔗 NCCN Head & Neck Guidelines"
        }
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
        return "⚠️ Treatment info unavailable for this stage."

    return treatment_dict.get(cancer_type, {}).get(stage_group, "⚠️ Treatment guidelines not available for this cancer type.")

# ------------------- Main Logic ------------------- #
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
                if question == "🧾 What is my cancer stage?":
                    st.markdown(f"Your cancer is staged as **{staging['Stage']}**.")
                elif question == "💊 What treatment is usually given?":
                    treatment = get_treatment_advice(features["cancer_type"], staging["Stage"])
                    st.markdown(treatment)
                elif question == "🧠 What does this mean in simple terms?":
                    st.markdown(generate_summary(staging["Stage"], features["cancer_type"]))
                elif question == "📥 Download full summary":
                    treatment = get_treatment_advice(features["cancer_type"], staging["Stage"])
                    explanation = generate_summary(staging["Stage"], features["cancer_type"])
                    summary_text = f"""Cancer Type: {features['cancer_type'].capitalize()}
Stage: {staging['Stage']}
TNM: T={staging['T']}, N={staging['N']}, M={staging['M']}

Explanation:
{explanation}

Treatment:
{treatment}
"""
                   st.download_button("📥 Download .txt Summary", summary_text, file_name="cancer_summary.txt")
increment_download_count()
st.markdown(f"🧾 **Downloads so far**: {get_download_count()}")


        else:
            st.error("❌ Cancer type could not be identified from the report.")


# ------------------- Feedback Buttons ------------------- #
st.subheader("💬 Was this summary helpful?")

col1, col2 = st.columns(2)
with col1:
    if st.button("👍 Yes, it helped"):
        st.success("✅ Thanks for your feedback!")
with col2:
    if st.button("👎 Not really"):
        st.info("Thanks! We'll keep improving the AI chatbot.")

