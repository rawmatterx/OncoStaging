import streamlit as st
import fitz  # PyMuPDF
import docx
import re
import os
from tnm_staging import determine_tnm_stage
from fpdf import FPDF  # using fpdf2
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"

st.set_page_config(page_title="Cancer Staging Chatbot", layout="centered")
st.title("🤖 Cancer Staging Chatbot")
st.markdown("Upload your PET/CT report to get a staging summary and ask questions.")

uploaded_file = st.file_uploader("📤 Upload PET/CT Report (.pdf or .docx)", type=["pdf", "docx"])

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
    msg = f"Based on the report, this appears to be {stage} {cancer_type.capitalize()} Cancer.\n\n"
    if "IV" in stage:
        msg += "This indicates advanced disease with distant spread.\n"
    elif "III" in stage:
        msg += "This is a locally advanced stage.\n"
    elif "II" in stage:
        msg += "This is an early regional stage.\n"
    else:
        msg += "This appears to be an early stage disease.\n"
    msg += "\nPlease consult your oncologist before making any treatment decisions."
    msg += "\n\nThis is an AI-generated summary and may not reflect the complete clinical context."
    return msg

def remove_emojis(text):
    return re.sub(r'[^
